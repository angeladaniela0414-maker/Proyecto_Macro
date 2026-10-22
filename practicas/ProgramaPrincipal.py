# ProgramaPrincipal.py

from ListaTarea import ListaTarea


def main():

    opcion = 0

    miLista = None

    while opcion != 5:

        print("\n**Menú de opciones**")
        print("1.- Agregar tarea")
        print("2.- Marcar tarea como completada")
        print("3.- Eliminar tarea")
        print("4.- Mostrar tareas")
        print("5.- Salir")

        try:

            opcion = int(input("Ingrese una opción: "))

            match opcion:

                case 1:
                    miLista = ListaTarea.agregar(miLista)

                case 2:
                    miLista = ListaTarea.marcarTareaComoCompletada(
                        miLista
                    )

                case 3:
                    miLista = ListaTarea.eliminarPorNombre(miLista)

                case 4:
                    print(ListaTarea.imprimir(miLista))

                case 5:
                    print("Usaste un programa bacán, hasta luego")

                case _:
                    print("Opción inválida")

        except ValueError:
            print("Error: debe ingresar un número")


main()