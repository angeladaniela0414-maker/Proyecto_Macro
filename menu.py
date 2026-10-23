from almacen import cargar_datos, construir_datos, guardar_sesiones, recuperar_sesiones
from generador import generar_horario, pendientes_de, contar_huecos
from horarios import Horario_semestre, Horario_estudiante, Horario_profesor, Horario_salon


def menu():
    datos = cargar_datos()
    asignaturas, profesores, salones, paralelos = construir_datos(datos)
    bloques = recuperar_sesiones(datos, asignaturas, profesores, salones, paralelos)
    periodo = datos['configuracion']['periodo_academico']

    while True:
        print('\n===== HORARIOS ULEAM =====')
        print('1. Semestres  2. Paralelos  3. Asignaturas')
        print('4. Generar todos  5. Consultar semestre  6. Consultar paralelo')
        print('7. Consultar profesor  8. Consultar salón  9. Generar un semestre')
        print('10. Materias pendientes  11. Ver huecos  0. Salir')
        opcion = input('Opción: ').strip()

        if opcion == '1':
            for s in datos['semestres']:
                print(f"{s['numero']} | {s['unidad']} | {s['paralelos']} paralelos")
        elif opcion == '2':
            for p in paralelos:
                print(p.identificador)
        elif opcion == '3':
            for a in asignaturas:
                print(f'{a.semestre} | {a.codigo} | {a.nombre}')
        elif opcion in ('4', '9'):
            if opcion == '4':
                if bloques and input('¿Reemplazar TODOS los horarios? (s/n): ').lower() != 's':
                    continue
                elegidos, anteriores = paralelos, []
            else:
                try:
                    numero = int(input('Semestre a generar: '))
                except ValueError:
                    print('Semestre inválido.')
                    continue
                elegidos = [p for p in paralelos if p.semestre == numero]
                if not elegidos:
                    print('Semestre inexistente.')
                    continue
                anteriores = [b for b in bloques if b.paralelo.semestre != numero]
                if len(anteriores) != len(bloques) and input('¿Reemplazar ese semestre? (s/n): ').lower() != 's':
                    continue
            nuevos = generar_horario(datos, asignaturas, profesores, salones, elegidos, anteriores)
            faltan = pendientes_de(nuevos, asignaturas, elegidos)
            for p, cod, nombre, horas in faltan:
                print(f'SIN ASIGNAR: {p} | {cod} | {nombre} | {horas} horas')
            if faltan and input('Horario incompleto. ¿Guardarlo igualmente? (s/n): ').lower() != 's':
                print('No se reemplazó el horario guardado.')
                continue
            bloques = nuevos
            guardar_sesiones(datos, bloques)
            print(f'Guardadas {len(bloques)} sesiones en datos_horario.json.')
        elif opcion in ('5', '6', '7', '8'):
            if not bloques:
                print('Primero genera un horario.')
                continue
            try:
                if opcion == '5':
                    horario = Horario_semestre(1, periodo, bloques, int(input('Semestre: ')))
                elif opcion == '6':
                    horario = Horario_estudiante(1, periodo, bloques, input('Paralelo: ').strip().upper())
                elif opcion == '7':
                    for p in profesores:
                        print(p.id_profesor, p.nombre)
                    id_prof = int(input('ID profesor: '))
                    prof = next((p for p in profesores if p.id_profesor == id_prof), None)
                    if prof is None:
                        print('Profesor no encontrado.')
                        continue
                    horario = Horario_profesor(1, periodo, bloques, prof)
                else:
                    for s in salones:
                        print(s.id_salon, s.nombre)
                    id_salon = int(input('ID salón: '))
                    salon = next((s for s in salones if s.id_salon == id_salon), None)
                    if salon is None:
                        print('Salón no encontrado.')
                        continue
                    horario = Horario_salon(1, periodo, bloques, salon)
                horario.imprimir_horario()
            except ValueError:
                print('Ingresa un ID o semestre válido.')
        elif opcion == '10':
            faltan = pendientes_de(bloques, asignaturas, paralelos)
            if not faltan:
                print('Todas las materias tienen sus horas asignadas.')
            for p, cod, nombre, horas in faltan:
                print(f'{p} | {cod} | {nombre} | faltan {horas} horas')
        elif opcion == '11':
            if not bloques:
                print('Todavía no hay horarios.')
                continue
            for p in paralelos:
                huecos = contar_huecos(bloques, p, datos['configuracion']['dias'])
                for dia, inicio, fin in huecos:
                    print(f'{p.identificador} | {dia} | hueco {inicio}-{fin}')
            print('Se muestran solo huecos ENTRE clases dentro de una jornada (no tiempos libres al final).')
        elif opcion == '0':
            break
        else:
            print('Opción no válida.')


if __name__ == '__main__':
    menu()
