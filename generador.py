"""Generación sencilla: sesiones de 2 o 3 h, dos jornadas y sin choques."""
from collections import Counter
from horarios import Bloque_horario


def duraciones(horas):
    """Divide 4 en 2+2, 5 en 3+2, 6 en 3+3, etc."""
    if horas < 2:
        return []
    partes = []
    while horas > 0:
        duracion = 2 if horas == 2 or horas == 4 else 3
        partes.append(duracion)
        horas -= duracion
    return partes


def contar_huecos(bloques, paralelo, dias):
    """Horas vacías entre la primera y última clase de cada jornada."""
    huecos = []
    for dia in dias:
        for inicio_jornada, fin_jornada in [('07:00', '12:00'), ('13:00', '18:00')]:
            clases = sorted((b for b in bloques if b.paralelo.identificador == paralelo.identificador
                             and b.dia == dia and b.hora_inicio >= inicio_jornada
                             and b.hora_fin <= fin_jornada), key=lambda b: b.hora_inicio)
            for anterior, siguiente in zip(clases, clases[1:]):
                if anterior.hora_fin < siguiente.hora_inicio:
                    huecos.append((dia, anterior.hora_fin, siguiente.hora_inicio))
    return huecos


def pendientes_de(bloques, asignaturas, paralelos):
    """Devuelve asignatura, paralelo y horas aún sin asignar."""
    pendientes = []
    for paralelo in paralelos:
        for materia in asignaturas:
            if materia.semestre != paralelo.semestre:
                continue
            cubiertas = sum(int(b.hora_fin[:2]) - int(b.hora_inicio[:2]) for b in bloques
                            if b.paralelo.identificador == paralelo.identificador
                            and b.asignatura.codigo == materia.codigo)
            if cubiertas < materia.horas_semana:
                pendientes.append((paralelo.identificador, materia.codigo, materia.nombre,
                                   materia.horas_semana - cubiertas))
    return pendientes


def generar_horario(datos, asignaturas, profesores, salones, paralelos, bloques_existentes=None):
    """Genera solo los paralelos pedidos, respetando los bloques existentes."""
    cfg = datos['configuracion']
    dias = cfg['dias']
    bloques = list(bloques_existentes or [])
    carga = Counter()
    for b in bloques:
        carga[b.profesor.id_profesor] += int(b.hora_fin[:2]) - int(b.hora_inicio[:2])

    tareas = [(paralelo, materia) for paralelo in paralelos for materia in asignaturas
              if materia.semestre == paralelo.semestre]
    tareas.sort(key=lambda t: (sum(p.puede_dictar(t[1]) for p in profesores),
                               t[1].tipo_salon == 'Aula_virtual'))

    for paralelo, materia in tareas:
        docentes = sorted((p for p in profesores if p.puede_dictar(materia)),
                          key=lambda p: carga[p.id_profesor])
        aulas = ([None] if materia.tipo_salon == 'Aula_virtual' else
                 [s for s in salones if s.disponibilidad
                  and s.capacidad >= cfg['estudiantes_por_paralelo']
                  and (s.tipo_salon == materia.tipo_salon or
                       (materia.tipo_salon == 'Laboratorio' and s.tipo_salon == 'Laboratorio_redes'))])
        # Se mantiene un solo profesor por materia y paralelo.
        for docente in docentes:
            partes = duraciones(materia.horas_semana)
            if carga[docente.id_profesor] + materia.horas_semana > docente.max_horas_semana:
                continue
            asignados = []
            for duracion in partes:
                opciones = []
                for ndia, dia in enumerate(dias):
                    # Evita dividir la misma materia en varias sesiones el mismo día.
                    if any(b.dia == dia for b in asignados):
                        continue
                    for jornada, (primera, ultima) in enumerate([(7, 12), (13, 18)]):
                        for hora in range(primera, ultima - duracion + 1):
                            inicio = f'{hora:02d}:00'
                            fin = f'{hora + duracion:02d}:00'
                            for aula in aulas:
                                candidato = Bloque_horario(dia, inicio, fin, aula, materia, docente, paralelo)
                                if any(candidato.tiene_conflicto_con(b) for b in bloques + asignados):
                                    continue
                                actuales = bloques + asignados
                                antes = len(contar_huecos(actuales, paralelo, [dia]))
                                despues = len(contar_huecos(actuales + [candidato], paralelo, [dia]))
                                mismas_jornada = [b for b in actuales if b.dia == dia
                                                  and b.paralelo.identificador == paralelo.identificador
                                                  and ((jornada == 0 and b.hora_inicio < '12:00') or
                                                       (jornada == 1 and b.hora_inicio >= '13:00'))]
                                pegada = any(b.hora_fin == inicio or b.hora_inicio == fin for b in mismas_jornada)
                                # Primero minimiza huecos; luego mañanas y comienzo temprano.
                                puntaje = (despues - antes, not pegada, jornada, ndia, hora)
                                opciones.append((puntaje, candidato))
                if not opciones:
                    break
                elegido = min(opciones, key=lambda x: x[0])[1]
                asignados.append(elegido)
            # No dejar media materia: si falla una sesión se prueba otro docente.
            if len(asignados) == len(partes) and partes:
                bloques.extend(asignados)
                carga[docente.id_profesor] += materia.horas_semana
                break

    pendientes = pendientes_de(bloques, asignaturas, paralelos)
    print(f'Sesiones nuevas: {len(bloques)-len(bloques_existentes or [])}. '
          f'Horas pendientes: {sum(p[3] for p in pendientes)}.')
    return bloques
