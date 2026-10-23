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
                print(s['numero'], s['unidad'], s['paralelos'], 'paralelos')
        elif opcion == '2':
            for paralelo in paralelos:
                print(paralelo)
        elif opcion == '3':
            for a in asignaturas:
                print(a.semestre, a.codigo, a.nombre)
        elif opcion == '4' or opcion == '9':
            if opcion == '4':
                if bloques and input('¿Reemplazar TODOS los horarios? (s/n): ').lower() != 's':
                    continue
                elegidos = paralelos
                anteriores = []
            else:
                try:
                    numero = int(input('Semestre a generar: '))
                except ValueError:
                    print('Semestre inválido.')
                    continue
                elegidos = []
                for paralelo in paralelos:
                    if int(paralelo[:-1]) == numero:
                        elegidos.append(paralelo)
                if not elegidos:
                    print('Semestre inexistente.')
                    continue
                anteriores = []
                for b in bloques:
                    if int(b.paralelo[:-1]) != numero:
                        anteriores.append(b)
                if len(anteriores) != len(bloques):
                    if input('¿Reemplazar ese semestre? (s/n): ').lower() != 's':
                        continue
            nuevos = generar_horario(datos, asignaturas, profesores, salones, elegidos, anteriores)
            faltan = pendientes_de(nuevos, asignaturas, elegidos)
            for paralelo, codigo, nombre, horas in faltan:
                print(f'SIN ASIGNAR: {paralelo} | {codigo} | {nombre} | {horas} horas')
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
                    numero = int(input('Semestre: '))
                    horario = Horario_semestre(1, periodo, bloques, numero)
                elif opcion == '6':
                    paralelo = input('Paralelo: ').strip().upper()
                    horario = Horario_estudiante(1, periodo, bloques, paralelo)
                elif opcion == '7':
                    for p in profesores:
                        print(p.id_profesor, p.nombre)
                    id_prof = int(input('ID profesor: '))
                    prof = None
                    for p in profesores:
                        if p.id_profesor == id_prof:
                            prof = p
                            break
                    if prof is None:
                        print('Profesor no encontrado.')
                        continue
                    horario = Horario_profesor(1, periodo, bloques, prof)
                else:
                    for s in salones:
                        print(s.id_salon, s.nombre)
                    id_salon = int(input('ID salón: '))
                    salon = None
                    for s in salones:
                        if s.id_salon == id_salon:
                            salon = s
                            break
                    if salon is None:
                        print('Salón no encontrado.')
                        continue
                    horario = Horario_salon(1, periodo, bloques, salon)
                horario.imprimir_horario()
            except ValueError:
                print('Ingresa un número válido.')
        elif opcion == '10':
            faltan = pendientes_de(bloques, asignaturas, paralelos)
            if not faltan:
                print('Todas las materias tienen sus horas asignadas.')
            for paralelo, codigo, nombre, horas in faltan:
                print(f'{paralelo} | {codigo} | {nombre} | faltan {horas} horas')
        elif opcion == '11':
            if not bloques:
                print('Todavía no hay horarios.')
                continue
            for paralelo in paralelos:
                huecos = contar_huecos(bloques, paralelo, datos['configuracion']['dias'])
                for dia, inicio, fin in huecos:
                    print(f'{paralelo} | {dia} | hueco {inicio}-{fin}')
        elif opcion == '0':
            break
        else:
            print('Opción no válida.')

if __name__ == '__main__':
    menu()
