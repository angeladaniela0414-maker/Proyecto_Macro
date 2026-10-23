"""Horarios de dos jornadas, sesiones de 2 o 3 horas y sin choques."""
from horarios import Bloque_horario

def duraciones(horas):
    if horas < 2:
        return []
    partes = []
    while horas > 0:
        duracion = 2 if horas in (2, 4) else 3
        partes.append(duracion)
        horas -= duracion
    return partes

def contar_huecos(bloques, paralelo, dias):
    huecos = []
    for dia in dias:
        for primera, ultima in [('07:00', '12:00'), ('13:00', '18:00')]:
            clases = []
            for b in bloques:
                if (b.paralelo == paralelo and b.dia == dia and
                    b.hora_inicio >= primera and b.hora_fin <= ultima):
                    clases.append(b)
            def hora_clase(b):
                return b.hora_inicio
            clases.sort(key=hora_clase)
            for i in range(len(clases) - 1):
                anterior = clases[i]
                siguiente = clases[i + 1]
                if anterior.hora_fin < siguiente.hora_inicio:
                    huecos.append((dia, anterior.hora_fin, siguiente.hora_inicio))
    return huecos

def pendientes_de(bloques, asignaturas, paralelos):
    pendientes = []
    for paralelo in paralelos:
        semestre = int(paralelo[:-1])
        for materia in asignaturas:
            if materia.semestre != semestre:
                continue
            cubiertas = 0
            for b in bloques:
                if b.paralelo == paralelo and b.materia.codigo == materia.codigo:
                    cubiertas += b.horas()
            if cubiertas < materia.horas_semana:
                pendientes.append((paralelo, materia.codigo, materia.nombre,
                                   materia.horas_semana - cubiertas))
    return pendientes

def generar_horario(datos, asignaturas, profesores, salones, paralelos, bloques_existentes=None):
    dias = datos['configuracion']['dias']
    bloques = list(bloques_existentes) if bloques_existentes is not None else []
    carga = {}
    for p in profesores:
        carga[p.id_profesor] = 0
    for b in bloques:
        carga[b.profesor.id_profesor] += b.horas()

    tareas = []
    for paralelo in paralelos:
        semestre = int(paralelo[:-1])
        for materia in asignaturas:
            if materia.semestre == semestre:
                tareas.append((paralelo, materia))

    # Primero las materias presenciales y con pocos profesores disponibles.
    def prioridad(tarea):
        materia = tarea[1]
        cantidad = 0
        for profesor in profesores:
            if profesor.puede_dictar(materia):
                cantidad += 1
        return (cantidad, materia.tipo_salon == 'Aula_virtual')
    tareas.sort(key=prioridad)

    for paralelo, materia in tareas:
        docentes = []
        for p in profesores:
            if p.puede_dictar(materia):
                docentes.append(p)
        def horas_docente(p):
            return carga[p.id_profesor]
        docentes.sort(key=horas_docente)
        aulas = []
        if materia.tipo_salon == 'Aula_virtual':
            aulas.append(None)
        else:
            for salon in salones:
                tipo_valido = (salon.tipo_salon == materia.tipo_salon or
                               (materia.tipo_salon == 'Laboratorio' and
                                salon.tipo_salon == 'Laboratorio_redes'))
                if (salon.disponibilidad and tipo_valido and
                    salon.capacidad >= datos['configuracion']['estudiantes_por_paralelo']):
                    aulas.append(salon)

        partes = duraciones(materia.horas_semana)
        for docente in docentes:
            if carga[docente.id_profesor] + materia.horas_semana > docente.max_horas_semana:
                continue
            asignados = []
            for duracion in partes:
                mejor = None
                mejor_puntaje = None
                for ndia, dia in enumerate(dias):
                    repetido = False
                    for b in asignados:
                        if b.dia == dia:
                            repetido = True
                            break
                    if repetido:
                        continue
                    for jornada, (primera, ultima) in enumerate([(7, 12), (13, 18)]):
                        for hora in range(primera, ultima - duracion + 1):
                            inicio = f'{hora:02d}:00'
                            fin = f'{hora + duracion:02d}:00'
                            for salon in aulas:
                                candidato = Bloque_horario(dia, inicio, fin, salon,
                                                           materia, docente, paralelo)
                                actuales = bloques + asignados
                                conflicto = False
                                for b in actuales:
                                    if candidato.tiene_conflicto_con(b):
                                        conflicto = True
                                        break
                                if conflicto:
                                    continue
                                antes = len(contar_huecos(actuales, paralelo, [dia]))
                                despues = len(contar_huecos(actuales + [candidato], paralelo, [dia]))
                                pegada = False
                                for b in actuales:
                                    if b.paralelo == paralelo and b.dia == dia:
                                        if b.hora_fin == inicio or b.hora_inicio == fin:
                                            pegada = True
                                            break
                                puntaje = (despues - antes, not pegada, jornada, ndia, hora)
                                if mejor_puntaje is None or puntaje < mejor_puntaje:
                                    mejor_puntaje = puntaje
                                    mejor = candidato
                if mejor is None:
                    break
                asignados.append(mejor)
            if partes and len(asignados) == len(partes):
                bloques.extend(asignados)
                carga[docente.id_profesor] += materia.horas_semana
                break

    pendientes = pendientes_de(bloques, asignaturas, paralelos)
    horas_pendientes = 0
    for pendiente in pendientes:
        horas_pendientes += pendiente[3]
    print(f'Sesiones nuevas: {len(bloques) - len(bloques_existentes or [])}. '
          f'Horas pendientes: {horas_pendientes}.')
    return bloques

