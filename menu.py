from datetime import datetime
import almacen
from horarios import (Salon, Bloque_horario, Asignatura)
print(">>> SE ESTÁ EJECUTANDO menu.py")
print(">>> ALMACEN IMPORTADO DESDE:", almacen.__file__)
print(">>> ¿EXISTE cargar?:", hasattr(almacen, "cargar"))

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


def crear_sesion(datos):
    asignaturas, salones, bloques = datos["asignaturas"], datos["salones"], datos["bloques"]
    print("\n=== CREAR SESIÓN ===")

    if not asignaturas or not salones:
        print("Primero debes registrar asignaturas y salones.")
        return

    asignatura = elegir_opcion(asignaturas, "Asignaturas")
    salon = elegir_opcion(salones, "Salones")

    profesor = elegir_opcion(datos["profesores"], "Profesores")
    paralelo = elegir_opcion(datos["paralelos"], "Paralelos")

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
        inicio.strftime("%H:%M"),   # normaliza "8:00" -> "08:00"
        fin.strftime("%H:%M"),
        salon,
        asignatura,
        profesor,
        paralelo
    )

    # Comprobar cruces con las sesiones existentes.
    for bloque in bloques:
        if nueva_sesion.se_cruza_con(bloque):
            print("No se puede registrar: existe un conflicto.")
            print("Sesión que entra en conflicto:")
            print(bloque)
            return

    bloques.append(nueva_sesion)
    almacen.guardar(datos)
    print("\n¡Sesión registrada correctamente!")
    print(nueva_sesion)
    
def mostrar_sesiones(bloques):
    print("\n=== SESIONES REGISTRADAS ===")

    if not bloques:
        print("Todavía no hay sesiones.")
        return

    for i, bloque in enumerate(bloques, start=1):
        print(f"{i}. {bloque}")

def eliminar_sesion(datos):
    bloques = datos["bloques"]
    if not bloques:
        print("No hay sesiones para eliminar.")
        return
    bloque = elegir_opcion(bloques, "Sesiones")
    bloques.remove(bloque)
    almacen.guardar(datos)
    print("Sesión eliminada.")


def agregar_asignatura(datos):
    nombre = input("Nombre de la asignatura: ").strip()
    try:
        semestre = int(input("Semestre: "))
    except ValueError:
        print("El semestre debe ser un número.")
        return
    nuevo_id = max([a.id_asignatura for a in datos["asignaturas"]], default=0) + 1
    datos["asignaturas"].append(Asignatura(nuevo_id, nombre, semestre))
    almacen.guardar(datos)
    print("Asignatura agregada.")


def agregar_salon(datos):
    nombre = input("Nombre del salón: ").strip()
    try:
        capacidad = int(input("Capacidad: "))
    except ValueError:
        print("La capacidad debe ser un número.")
        return
    tipo = input("Tipo (Aula/Laboratorio): ").strip() or "Aula"
    nuevo_id = max([s.id_salon for s in datos["salones"]], default=0) + 1
    datos["salones"].append(Salon(nuevo_id, nombre, capacidad, tipo))
    almacen.guardar(datos)
    print("Salón agregado.")


def eliminar_asignatura(datos):
    if not datos["asignaturas"]:
        print("No hay asignaturas.")
        return
    asignatura = elegir_opcion(datos["asignaturas"], "Asignaturas")
    if any(b.asignatura is asignatura for b in datos["bloques"]):
        print("No se puede eliminar: tiene sesiones registradas.")
        return
    datos["asignaturas"].remove(asignatura)
    almacen.guardar(datos)
    print("Asignatura eliminada.")


def eliminar_salon(datos):
    if not datos["salones"]:
        print("No hay salones.")
        return
    salon = elegir_opcion(datos["salones"], "Salones")
    if any(b.salon is salon for b in datos["bloques"]):
        print("No se puede eliminar: tiene sesiones registradas.")
        return
    datos["salones"].remove(salon)
    almacen.guardar(datos)
    print("Salón eliminado.")


def submenu(datos, clave, agregar, eliminar):
    mostrar_opciones(datos[clave], clave.capitalize())
    accion = input("¿(a)gregar, (e)liminar o Enter para volver?: ").strip().lower()
    if accion == "a":
        agregar(datos)
    elif accion == "e":
        eliminar(datos)


def menu():
    print("entrando")
    datos = almacen.cargar()
    print("RESULTADO DE cargar():", repr(datos))

    while True:
        print("\n===== SISTEMA DE HORARIOS =====")
        print("1. Crear sesión")
        print("2. Mostrar sesiones")
        print("3. Eliminar sesión")
        print("4. Ver / agregar / eliminar asignaturas")
        print("5. Ver / agregar / eliminar salones")
        print("0. Salir")

        opcion = input("Selecciona una opción: ").strip()

        if opcion == "1":
            crear_sesion(datos)

        elif opcion == "2":
            mostrar_sesiones(datos["bloques"])

        elif opcion == "3":
            eliminar_sesion(datos)

        elif opcion == "4":
            submenu(datos, "asignaturas", agregar_asignatura, eliminar_asignatura)

        elif opcion == "5":
            submenu(datos, "salones", agregar_salon, eliminar_salon)

        elif opcion == "0":
            print("Saliendo del sistema...")
            break

        else:
            print("Opción no válida.")


if __name__ == "__main__":
    menu()
