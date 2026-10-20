# Lee y guarda los datos. Cuando pasen a base de datos, solo se cambia este archivo.
import json
from horarios import Asignatura, Salon, Bloque_horario
from pathlib import Path

CARPETA = Path(__file__).resolve().parent
ARCHIVO = CARPETA / "datos_horario.json"


def cargar():
    with open(ARCHIVO, "r", encoding="utf-8") as f:
        d = json.load(f)

    asignaturas = [
        Asignatura(**a) for a in d["asignaturas"]
    ]

    salones = [
        Salon(**s) for s in d["salones"]
    ]

    por_asig = {
        a.id_asignatura: a for a in asignaturas
    }

    por_salon = {
        s.id_salon: s for s in salones
    }

    bloques = []

    for b in d["bloques"]:
        nuevo_bloque = Bloque_horario(
            b["dia"],
            b["hora_inicio"],
            b["hora_fin"],
            por_salon[b["id_salon"]],
            por_asig[b["id_asignatura"]],
            b["profesor"],
            b["paralelo"]
        )

        bloques.append(nuevo_bloque)

    datos = {
        "periodo_academico": d["periodo_academico"],
        "profesores": [
            p["nombre"] for p in d["profesores"]
        ],
        "paralelos": [
            p["nombre"] for p in d["paralelos"]
        ],
        "asignaturas": asignaturas,
        "salones": salones,
        "bloques": bloques
    }

    return datos

  

def guardar(datos):
    d = {
        "periodo_academico": datos["periodo_academico"],
        "profesores": [{"id_profesor": i, "nombre": n} for i, n in enumerate(datos["profesores"], 1)],
        "paralelos": [{"id_paralelo": i, "nombre": n} for i, n in enumerate(datos["paralelos"], 1)],
        "asignaturas": [vars(a) for a in datos["asignaturas"]],
        "salones": [vars(s) for s in datos["salones"]],
        "bloques": [
            {"dia": b.dia, "hora_inicio": b.hora_inicio, "hora_fin": b.hora_fin,
             "id_asignatura": b.asignatura.id_asignatura, "id_salon": b.salon.id_salon,
             "profesor": b.profesor, "paralelo": b.paralelo}
            for b in datos["bloques"]
        ],
    }
    with open(ARCHIVO, "w", encoding="utf-8") as f:
        json.dump(d, f, indent=2, ensure_ascii=False)

