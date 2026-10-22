class Gestion_Academica:
    horas_administrativas = 120

    def __init__(self, facultad, cargo, carrera):
        self.facultad = facultad
        self.cargo = cargo
        self.carrera = carrera

    def asignarHorario(self, horas_docente):
        return horas_docente <= self.horas_administrativas

    @classmethod
    def registroPermisos(cls, hora_limite):
        return cls.horas_administrativas <= hora_limite

    @staticmethod
    def rol(facultad, cargo, carrera):
        return f"{facultad.title()} {cargo.title()} {carrera.title()}"


consulta = Gestion_Academica("ciencias", "secretaria", "software")
print(consulta.facultad)
print(consulta.cargo)
print(consulta.carrera)
print(consulta.asignarHorario(100))
print(Gestion_Academica.registroPermisos(150))
print(Gestion_Academica.rol("ciencias", "secretaria", "software"))



class Docente:
    horas_max_semana = 40  # atributo de clase

    def __init__(self, cedula, nombre, apellido, especialidad, asignatura, nivel):
        self.cedula = cedula  # atributo de instancia
        self.nombre = nombre
        self.apellido = apellido
        self.especialidad = especialidad
        self.asignatura = asignatura
        self.nivel = nivel

    # Método de instancia
    def puede_tomar_horas(self, horas_asignadas):
        return horas_asignadas <= self.horas_max_semana

    # Método de clase
    @classmethod
    def cambiar_horas_max(cls, nuevo_limite):
        cls.horas_max_semana = nuevo_limite

    # Método estático
    @staticmethod
    def nombre_completo(nombre, apellido):
        return f"{nombre.title()} {apellido.title()}"


docente1 = Docente("1300000001", "juan", "perez", "sistemas", "programacion", "cuarto")
print(docente1.nombre)
print(docente1.asignatura)
print(docente1.puede_tomar_horas(35))
print(Docente.nombre_completo("juan", "perez"))
Docente.cambiar_horas_max(30)  # cambio del atributo de clase
print(docente1.puede_tomar_horas(35))  # el objeto también cambia


class Estudiante:
    nivel = "cuarto"

    def __init__(self, codigo, nombre, apellido, correo, curso, nivel):
        print(f"creamos al usuario del estudiante {nombre} {apellido}")
        self.__codigo = codigo
        self.nombre = nombre
        self.apellido = apellido
        self.correo = correo
        self.curso = curso
        self.nivel = nivel

    def consultar_nivel(self, nivel_actual):
        return nivel_actual == self.nivel

    @classmethod
    def desde_texto(cls, texto):
        codigo, nombre, apellido, correo, curso, nivel = texto.split(",")
        return cls(codigo, nombre, apellido, correo, curso, nivel)

    @staticmethod
    def es_correo_institucional(correo):
        arroba = "@universidad.edu.ec"
        return correo.endswith(arroba)


estudiante1 = Estudiante("E001", "ana", "lopez", "ana@universidad.edu.ec", "A", "cuarto")
print(estudiante1.nombre)
print(estudiante1.consultar_nivel("cuarto"))
estudiante2 = Estudiante.desde_texto("E002,luis,mora,luis@gmail.com,B,tercero")
print(estudiante2.nombre)
print(Estudiante.es_correo_institucional(estudiante1.correo))
print(Estudiante.es_correo_institucional(estudiante2.correo))



class Horario:
    hora_limite = 20  # atributo de clase

    def __init__(self, dia, hora_inicio, hora_fin, periodo, nivel):
        self.dia = dia
        self.hora_inicio = hora_inicio
        self.hora_fin = hora_fin
        self.periodo = periodo
        self.nivel = nivel

    def duracion(self):
        return self.hora_fin - self.hora_inicio

    @classmethod
    def cambiar_hora_limite(cls, nueva_hora):
        cls.hora_limite = nueva_hora

    @staticmethod
    def es_hora_valida(hora_inicio, hora_fin):
        return hora_fin > hora_inicio


horario1 = Horario("lunes", 8, 10, "2026-1", "cuarto")
print(horario1.dia)
print(horario1.duracion())
print(Horario.es_hora_valida(8, 10))
print(horario1.hora_limite)
Horario.cambiar_hora_limite(18)  # cambio del atributo de clase
print(horario1.hora_limite)  # el objeto ya creado también cambia
print()


class Registro:
    estado_inicial = "pendiente"  # atributo de clase

    def __init__(self, cedulaEstudiante, codigoDeRegistro, fechaaRegistro, estado):
        self.cedulaEstudiante = cedulaEstudiante
        self.codigoDeRegistro = codigoDeRegistro
        self.fechaaRegistro = fechaaRegistro
        self.estado = estado

    def cambiar_estado(self, nuevo_estado):
        self.estado = nuevo_estado

    @classmethod
    def cambiar_estado_inicial(cls, nuevo_estado):
        cls.estado_inicial = nuevo_estado

    @staticmethod
    def cedula_valida(cedula):
        return len(cedula) == 10


registro1 = Registro("1300000002", "R001", "2026-09-29", "pendiente")
print(registro1.cedulaEstudiante)
print(registro1.estado)
registro1.cambiar_estado("aprobado")
print(registro1.estado)
print(Registro.cedula_valida(registro1.cedulaEstudiante))
print(registro1.estado_inicial)
Registro.cambiar_estado_inicial("revision")  # cambio del atributo de clase
print(registro1.estado_inicial)  # el objeto ya creado también cambia
print()
