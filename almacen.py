"""Acceso a datos. Al migrar a BD, reemplazar las funciones de este módulo."""
import json
from pathlib import Path
from horarios import Asignatura, Salon, Paralelo, Profesor, Bloque_horario

ARCHIVO = Path(__file__).resolve().parent / 'datos_horario.json'


def cargar_datos():
    with ARCHIVO.open('r', encoding='utf-8') as archivo:
        return json.load(archivo)


def construir_datos(datos):
    asignaturas = [
        Asignatura(m['codigo'], m['nombre'], m['semestre'], m['codigo'],
                   m.get('area', ''), m.get('tipo_salon', 'Aula'),
                   m.get('horas_semana', 3))
        for m in datos['materias']
    ]
    profesores = [
        Profesor(p['id_profesor'], p['nombre'], p['materias'],
                 p.get('max_horas_semana', 24))
        for p in datos['profesores']
    ]
    salones = [
        Salon(s['id_salon'], s['nombre'], s['capacidad'],
              s['tipo_salon'], s['disponibilidad'])
        for s in datos['salones']
    ]
    paralelos = [
        Paralelo(f"{s['numero']}{chr(65 + i)}", s['numero'])
        for s in datos['semestres'] for i in range(s['paralelos'])
    ]
    return asignaturas, profesores, salones, paralelos


def guardar_sesiones(datos, bloques):
    datos['sesiones'] = [
        {'dia': b.dia, 'hora_inicio': b.hora_inicio, 'hora_fin': b.hora_fin,
         'codigo_asignatura': b.asignatura.codigo,
         'id_profesor': b.profesor.id_profesor,
         'id_salon': b.salon.id_salon if b.salon else None,
         'paralelo': b.paralelo.identificador}
        for b in bloques
    ]
    horarios = datos.setdefault('horarios', {})
    horarios['por_paralelo'] = {}
    horarios['por_semestre'] = {}
    for b in bloques:
        horarios['por_paralelo'].setdefault(b.paralelo.identificador, []).append(
            f'{b.dia} {b.hora_inicio}-{b.hora_fin} | {b.asignatura.codigo}'
        )
        horarios['por_semestre'].setdefault(str(b.paralelo.semestre), []).append(
            f'{b.paralelo.identificador} | {b.dia} {b.hora_inicio}-{b.hora_fin} | {b.asignatura.codigo}'
        )
    with ARCHIVO.open('w', encoding='utf-8') as archivo:
        json.dump(datos, archivo, ensure_ascii=False, indent=2)


def recuperar_sesiones(datos, asignaturas, profesores, salones, paralelos):
    materias = {a.codigo: a for a in asignaturas}
    docentes = {p.id_profesor: p for p in profesores}
    aulas = {s.id_salon: s for s in salones}
    grupos = {p.identificador: p for p in paralelos}
    bloques = []
    for sesion in datos.get('sesiones', []):
        try:
            bloques.append(Bloque_horario(
                sesion['dia'], sesion['hora_inicio'], sesion['hora_fin'],
                aulas.get(sesion['id_salon']), materias[sesion['codigo_asignatura']],
                docentes[sesion['id_profesor']], grupos[sesion['paralelo']]
            ))
        except (KeyError, TypeError) as exc:
            print(f'Advertencia: sesión guardada inválida ({exc}).')
    return bloques
