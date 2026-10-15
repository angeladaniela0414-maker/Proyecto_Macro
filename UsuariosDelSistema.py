from abc import ABCMeta, abstractmethod

#Creando la clase abstracta usuario
class Usuario(metaclass=ABCMeta):
    def __init__(self, usuario, password, identificacion):
        self.usuario = usuario
        self.password = password
        self.id = identificacion


    @abstractmethod
    def iniciarSesion():
        pass

    @abstractmethod
    def cerrarSesion():
        pass


#Creando las clases hijas de usuario
class Administrador(Usuario):
    def __init__(self, usuario, password, identificacion, nivelAcceso):
        super().__init__(usuario, password, identificacion)
        self.nivelAcceso = nivelAcceso

    def soporteBaseDeDatos():
        pass
    
    def gestionarUsuarios():
        pass
    
    def asignarRoles():
        pass
    
    def registrarDocente():
        pass
    
    def modificarDocente():
        pass
    
    def eliminarDocente():
        pass
    
    def registrarEstudiante():
        pass
    
    def eliminarEstudiante():
        pass
    
    def modificarHorario():
        pass


class GestionAcademica(Usuario):
    def __init__(self, usuario, password, identificacion, nombre, apellido, facultad, carrera, cargo):
        super().__init__(usuario, password, identificacion)

        self.nombre = nombre
        self.apellido = apellido
        self.facultad = facultad
        self.carrera = carrera
        self.cargo = cargo

    def generarHorario():
        pass

    def asignarHorario():
        pass

    def consultarDocentes():
        pass

    def consultarEstudiantes():
        pass

    def recuperarPassword():
        pass

class Docente(Usuario):
    def __init__(self, usuario, password, identificacion, cedula, nombre, apellido, especialidad, nivel, estado):
        super().__init__(usuario, password, identificacion)
        
        self.cedula = cedula
        self.nombre = nombre
        self.apellido = apellido
        self.especialidad = especialidad
        self.nivel = nivel
        self.estado = estado
        self.asignaturas = []

    def recuperarPassword():
        pass

    def mostrarHorario():
        pass

    def verTutorias():
        pass

    def consultarEstudiantes():
        pass

    def filtrarAsignatura():
        pass

class Estudiante(Usuario):
    def __init__(self, usuario, password, identificacion, correoInstitucional, nombre, apellido, curso, carrera, nivel):
        super().__init__(usuario, password, identificacion)

        self.correoInstitucional = correoInstitucional
        self.nombre = nombre
        self.apellido = apellido
        self.curso = curso
        self.carrera =carrera
        self.nivel = nivel
        self.asignaturas = []

    def verTutorias():
        pass

    def filtrarParalelo():
        pass

    def filtrarNivel():
        pass

    def mostrarHorario():
        pass

    def recuperarPassword():
        pass

