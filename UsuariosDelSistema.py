from abc import ABCMeta, abstractmethod

#Creando la clase abstracta usuario
class Usuario(metaclass=ABCMeta):
    def __init__(self, id, correoInstitucional, password, nombre, apellido, carrera):
        self.id = id
        self.correoInstitucional = correoInstitucional
        self._password = password
        self.nombre = nombre
        self.apellido = apellido
        self.carrera = carrera
        self.estadoSistema = False


    @abstractmethod
    def iniciarSesion(self):
        pass

    @abstractmethod
    def cerrarSesion(self):
        pass

    @abstractmethod
    def mostrarMenu():
        pass


#Creando las clases hijas de usuario

class GestionAcademica(Usuario):
    def __init__(self, id, correoInstitucional, password, nombre, carrera, apellido, facultad,  cargo):
        super().__init__(id, correoInstitucional, password, nombre, carrera, apellido)

        self.facultad = facultad
        self.cargo = cargo

    def iniciarSesion(self):
        pass

    def cerrarSesion(self):
        pass

    def generarHorario(self):
        pass

    def asignarHorario(self):
        pass

    def consultarDocentes(self):
        pass

    def consultarEstudiantes(self):
        pass

    def recuperarPassword(self):
        pass

class Docente(Usuario):
    def __init__(self, id, correoInstitucional, password, nombre, apellido, carrera, cedula, especialidad, nivel, estado):
        super().__init__(id, correoInstitucional, password, nombre, apellido, carrera)
        
        self.cedula = cedula
        self.especialidad = especialidad
        self.nivel = nivel
        self.estado = estado
        self.asignaturas = []

    def iniciarSesion(self):
        pass

    def cerrarSesion(self):
        pass

    def recuperarPassword(self):
        pass

    def mostrarHorario(self):
        pass

    def verTutorias(self):
        pass

    def consultarEstudiantes(self):
        pass

    def filtrarAsignatura(self):
        pass

class Estudiante(Usuario):
    def __init__(self, id, correoInstitucional, password, nombre, apellido, curso, carrera, nivel):
        super().__init__(id, correoInstitucional, password, nombre, apellido, carrera)

        self.curso = curso
        self.nivel = nivel
        self.asignaturas = []

    def iniciarSesion(self):
        pass

    def cerrarSesion(self):
        pass

    def verTutorias(self):
        pass

    def filtrarParalelo(self):
        pass

    def filtrarNivel(self):
        pass

    def mostrarHorario(self):
        pass

    def recuperarPassword(self):
        pass
