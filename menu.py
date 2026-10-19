from datetime import datetime
import json

from horarios import (Salon, Bloque_horario, Asignatura)

def mostrar_opciones(lista, nombre):
    print(f"\n--- {nombre} disponibles ---")

    for i, elemento in enumerate(lista, start=1):
        print(f"{i}. {elemento}")


def elegir_opcion(lista, nombre):
    mostrar_opciones(lista, nombre)

    while True:
        try:
            opcion = int(input("Selecciona una opción: "))

            if 1 <= opcion <= len(lista):
                return lista[opcion - 1]

            print("Opción fuera de rango.")

        except ValueError:
            print("Debes ingresar un número.")


def crear_sesion(asignaturas, salones, bloques):
    print("\n=== CREAR SESIÓN ===")

    if not asignaturas or not salones:
        print("Primero debes registrar asignaturas y salones.")
        return

    asignatura = elegir_opcion(asignaturas, "Asignaturas")
    salon = elegir_opcion(salones, "Salones")

    profesor = input("Nombre del profesor: ").strip()
    paralelo = input("Paralelo (ej. 3A): ").strip()

    dias = [
        "Lunes", "Martes", "Miércoles",
        "Jueves", "Viernes"
    ]

    dia = elegir_opcion(dias, "Días")

    hora_inicio = input("Hora de inicio (HH:MM): ").strip()
    hora_fin = input("Hora de fin (HH:MM): ").strip()

    # Comprobar el formato y el orden de las horas.
    try:
        inicio = datetime.strptime(hora_inicio, "%H:%M")
        fin = datetime.strptime(hora_fin, "%H:%M")
    except ValueError:
        print("Formato incorrecto. Ejemplo válido: 08:00.")
        return

    if inicio >= fin:
        print("La hora de fin debe ser posterior a la de inicio.")
        return

    nueva_sesion = Bloque_horario(
        dia,
        hora_inicio,
        hora_fin,
        salon,
        asignatura,
        profesor,
        paralelo
    )

    # Comprobar cruces con las sesiones existentes.
    for bloque in bloques:
        if nueva_sesion.se_cruza_con(bloque):
            mismo_profesor = nueva_sesion.profesor == bloque.profesor
            mismo_paralelo = nueva_sesion.paralelo == bloque.paralelo
            mismo_salon = (nueva_sesion.salon.id_salon== bloque.salon.id_salon)

            if mismo_profesor or mismo_paralelo or mismo_salon:
                print("No se puede registrar: existe un conflicto.")
                print("Sesión que entra en conflicto:")
                print(bloque)
                return

    bloques.append(nueva_sesion)
    print("\n¡Sesión registrada correctamente!")
    print(nueva_sesion)
    
def mostrar_sesiones(bloques):
    print("\n=== SESIONES REGISTRADAS ===")

    if not bloques:
        print("Todavía no hay sesiones.")
        return

    for i, bloque in enumerate(bloques, start=1):
        print(f"{i}. {bloque}")

def menu():
    # Datos de prueba
    asignaturas = [
        Asignatura(1, "Programación", 3),
        Asignatura(2, "Base de Datos", 3),
        Asignatura(3, "Redes de Computadoras", 3)
    ]

    salones = [
        Salon(1, "Laboratorio 1", 30, "Laboratorio"),
        Salon(2, "Aula 2", 40, "Aula")
    ]

    # Aquí se guardan las sesiones creadas.
    bloques = []

    while True:
        print("\n===== SISTEMA DE HORARIOS =====")
        print("1. Crear sesión")
        print("2. Mostrar sesiones")
        print("3. Ver asignaturas")
        print("4. Ver salones")
        print("0. Salir")

        opcion = input("Selecciona una opción: ").strip()

        if opcion == "1":
            crear_sesion(asignaturas, salones, bloques)

        elif opcion == "2":
            mostrar_sesiones(bloques)

        elif opcion == "3":
            mostrar_opciones(asignaturas, "Asignaturas")

        elif opcion == "4":
            mostrar_opciones(salones, "Salones")

        elif opcion == "0":
            print("Saliendo del sistema...")
            break

        else:
            print("Opción no válida.")


if __name__ == "__main__":
    menu()