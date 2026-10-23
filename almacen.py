import json
from pathlib import Path
from horarios import Materia, Salon, Profesor, Bloque_horario

ARCHIVO = Path(__file__).resolve().parent / 'datos_horario.json'

def cargar_datos():
    with ARCHIVO.open('r', encoding='utf-8') as archivo:
        return json.load(archivo)

def construir_datos(datos):
    asignaturas = []
    for m in datos['materias']:
        asignatura = Materia(m['codigo'], m['nombre'], m['semestre'],
                            m.get('area', ''), m.get('tipo_salon', 'Aula'),
                            m.get('horas_semana', 3))
        asignaturas.append(asignatura)

    profesores = []
    for p in datos['profesores']:
        profesor = Profesor(p['id_profesor'], p['nombre'], p['materias'],
                            p.get('max_horas_semana', 20))
        profesores.append(profesor)

    salones = []
    for s in datos['salones']:
        salon = Salon(s['id_salon'], s['nombre'], s['capacidad'],
                      s['tipo_salon'], s['disponibilidad'])
        salones.append(salon)

    paralelos = []
    for semestre in datos['semestres']:
        for i in range(semestre['paralelos']):
            letra = chr(65 + i)
            paralelos.append(str(semestre['numero']) + letra)
    return asignaturas, profesores, salones, paralelos

def guardar_sesiones(datos, bloques):
    datos['sesiones'] = []
    datos['horarios'] = {'por_paralelo': {}, 'por_semestre': {}}
    for b in bloques:
        id_salon = b.salon.id_salon if b.salon is not None else None
        datos['sesiones'].append({
            'dia': b.dia, 'hora_inicio': b.hora_inicio, 'hora_fin': b.hora_fin,
            'codigo_asignatura': b.materia.codigo, 'id_profesor': b.profesor.id_profesor,
            'id_salon': id_salon, 'paralelo': b.paralelo
        })
        por_paralelo = datos['horarios']['por_paralelo']
        por_semestre = datos['horarios']['por_semestre']
        semestre = str(b.materia.semestre)
        if b.paralelo not in por_paralelo:
            por_paralelo[b.paralelo] = []
        if semestre not in por_semestre:
            por_semestre[semestre] = []
        resumen = f'{b.dia} {b.hora_inicio}-{b.hora_fin} | {b.materia.codigo}'
        por_paralelo[b.paralelo].append(resumen)
        por_semestre[semestre].append(f'{b.paralelo} | {resumen}')
    with ARCHIVO.open('w', encoding='utf-8') as archivo:
        json.dump(datos, archivo, ensure_ascii=False, indent=2)
    print('JSON guardado en:', ARCHIVO)

def recuperar_sesiones(datos, asignaturas, profesores, salones, paralelos):
    bloques = []
    for sesion in datos.get('sesiones', []):
        materia = None
        profesor = None
        salon = None
        for a in asignaturas:
            if a.codigo == sesion['codigo_asignatura']:
                materia = a
                break
        for p in profesores:
            if p.id_profesor == sesion['id_profesor']:
                profesor = p
                break
        for s in salones:
            if s.id_salon == sesion['id_salon']:
                salon = s
                break
        if materia is None or profesor is None or sesion['paralelo'] not in paralelos:
            print('Advertencia: se omitió una sesión con datos inexistentes.')
            continue
        bloques.append(Bloque_horario(sesion['dia'], sesion['hora_inicio'],
                                     sesion['hora_fin'], salon, materia,
                                     profesor, sesion['paralelo']))
    return bloques
