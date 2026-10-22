from abc import ABC, abstractmethod
from typing import List


# ==========================================
# CLASE ABSTRACTA BASE
# ==========================================

class Usuario(ABC):
    """
    Clase abstracta base para todos los usuarios del sistema académico.
    """
    def __init__(self, id_usuario: int, usuario: str, contrasena: str):
        self._id = id_usuario              # Atributo protegido (#)
        self._usuario = usuario            # Atributo protegido (#)
        self.__contrasena = contrasena      # Atributo privado (-)

    @property
    def id_usuario(self) -> int:
        return self._id

    @property
    def usuario(self) -> str:
        return self._usuario

    @property
    def contrasena(self) -> str:
        return self.__contrasena

    @contrasena.setter
    def contrasena(self, nueva_contrasena: str):
        if len(nueva_contrasena) >= 6:
            self.__contrasena = nueva_contrasena
        else:
            raise ValueError("La contraseña debe tener al menos 6 caracteres.")

    def ingresar(self) -> bool:
        print(f"Usuario {self._usuario} ha ingresado al sistema.")
        return True

    @abstractmethod
    def recuperarContrasena(self) -> None:
        """Método abstracto que obliga a implementar la recuperación según el tipo de usuario."""
        pass


# ==========================================
# ESPECIALIZACIONES DE USUARIO
# ==========================================

class GestionAcademica(Usuario):
    def __init__(self, id_usuario: int, usuario: str, contrasena: str, cedula: int,
                 nombre: str, facultad: str, cargo: str, carrera: str):
        super().__init__(id_usuario, usuario, contrasena)
        self.cedula = cedula
        self.nombre = nombre
        self.facultad = facultad
        self.cargo = cargo
        self.carrera = carrera

    def recuperarContrasena((self) -> None:
        print(f"[Gestión Académica] Instrucciones enviadas al correo institucional de {self.nombre}.")

    def asignarHorario(self) -> None:
        print("Horario asignado exitosamente.")

    def generarHorario(self) -> None:
        print("Horario general generado.")

    def consultarDocentes(self) -> List[str]:
        print("Consultando lista de docentes...")
        return []

    def consultarEstudiantes(self) -> List[str]:
        print("Consultando lista de estudiantes...")
        return []

    def generarReportes(self) -> None:
        print("Reportes académicos generados.")

    def generarArchivoHorario(self) -> None:
        print("Archivo de horario exportado.")

    def crearUsuarioEstudiante(self, datos_estudiante: dict) -> None:
        print("Nuevo usuario estudiante creado.")


class Docente(Usuario):
    def __init__(self, id_usuario: int, usuario: str, contrasena: str, cedula: int,
                 nombre: str, apellido: str, especialidad: str, asignatura: str,
                 nivel: int, estado: bool):
        super().__init__(id_usuario, usuario, contrasena)
        self.cedula = cedula
        self.nombre = nombre
        self.apellido = apellido
        self.especialidad = especialidad
        self.asignatura = asignatura
        self.nivel = nivel
        self.estado = estado

    def recuperarContrasena(self) -> None:
        print(f"[Docente] Enlace de restablecimiento enviado a {self.usuario}@unimail.edu.")

    def verTutorias(self) -> None:
        print(f"Desplegando horario de tutorías de {self.nombre} {self.apellido}.")

    def consultarEstudiantes(self) -> List[str]:
        print(f"Obteniendo nómina de estudiantes inscritos en {self.asignatura}.")
        return []


class Estudiante(Usuario):
    def __init__(self, id_usuario: int, usuario: str, contrasena: str, codigo_registro: int,
                 nombre: str, apellido: str, correo_institucional: str, curso: str,
                 carrera: str, nivel: int, asignatura: str):
        super().__init__(id_usuario, usuario, contrasena)
        self.codigo_registro = codigo_registro
        self.nombre = nombre
        self.apellido = apellido
        self.correo_institucional = correo_institucional
        self.curso = curso
        self.carrera = carrera
        self.nivel = nivel
        self.asignatura = asignatura

    def recuperarContrasena(self) -> None:
        print(f"[Estudiante] Código de verificación enviado al correo {self.correo_institucional}.")

    def filtrarNivel(self, nivel: int) -> None:
        print(f"Filtrando oferta académica por nivel {nivel}.")

    def filtrarCarrera(self, carrera: str) -> None:
        print(f"Filtrando información para la carrera {carrera}.")

    def filtrarParalelo(self, paralelo: str) -> None:
        print(f"Filtrando por paralelo {paralelo}.")

    def verTutorias(self) -> None:
        print("Consultando tutorías agendadas para el estudiante.")


class Administrador(Usuario):
    def __init__(self, id_usuario: int, usuario: str, contrasena: str, nivel_acceso: int):
        super().__init__(id_usuario, usuario, contrasena)
        self.nivel_acceso = nivel_acceso

    def recuperarContrasena(self) -> None:
        print("[Administrador] Contacte al departamento de infraestructura técnica para reajuste de credenciales.")

    def gestionUsuarios(self) -> None:
        print("Módulo de administración de usuarios activo.")

    def asignacionRoles(self) -> None:
        print("Actualizando permisos y roles de usuarios.")

    def reporteNivel(self) -> None:
        print("Generando reporte sistémico por niveles académicos.")

    def soporteBaseDeDatos(self) -> None:
        print("Ejecutando mantenimiento y respaldo de base de datos.")

    def ingresarContrasena(self) -> bool:
        print("Validación de seguridad avanzada para administrador.")
        return True


# ==========================================
# INFRAESTRUCTURA Y ENTIDADES
# ==========================================

class Salon:
    def __init__(self, numero_de_salon: int, capacidad: int, tipo_salon: str, estado: str):
        self.numero_de_salon = numero_de_salon
        self.capacidad = capacidad
        self.tipo_salon = tipo_salon
        self.estado = estado

    def consultarDisponibilidad(self) -> bool:
        return self.estado.lower() == "disponible"

    def asignarSalon(self) -> None:
        self.estado = "Ocupado"
        print(f"Salón {self.numero_de_salon} asignado.")

    def liberarSalon(self) -> None:
        self.estado = "Disponible"
        print(f"Salón {self.numero_de_salon} liberado.")


class Tutoria:
    def __init__(self, nombre: str, dia: int, hora: int):
        self.nombre = nombre
        self.dia = dia
        self.hora = hora


class Horario:
    def __init__(self, dia: str, hora_inicio: float, hora_fin: float, periodo: str,
                 nivel: str, asignatura: str, paralelo: str):
        self.dia = dia
        self.hora_inicio = hora_inicio
        self.hora_fin = hora_fin
        self.periodo = periodo
        self.nivel = nivel
        self.asignatura = asignatura
        self.paralelo = paralelo

    def consultarHorario(self) -> None:
        print(f"Horario: {self.dia} {self.hora_inicio} - {self.hora_fin} | {self.asignatura}")

    def imprimirHorario(self) -> None:
        print("Imprimiendo horario general...")

    def validarCruceHorario(self, otro_horario: 'Horario') -> bool:
        if self.dia == otro_horario.dia:
            if not (self.hora_fin <= otro_horario.hora_inicio or self.hora_inicio >= otro_horario.hora_fin):
                print("¡Atención! Se ha detectado un cruce de horarios.")
                return True
        return False


class HorarioDocente(Horario):
    def __init__(self, dia: str, hora_inicio: float, hora_fin: float, periodo: str,
                 nivel: str, asignatura: str, paralelo: str, salon: str):
        super().__init__(dia, hora_inicio, hora_fin, periodo, nivel, asignatura, paralelo)
        self.salon = salon

    def consultarHorasLibres(self) -> List[str]:
        print("Consultando bloques de horas libres del docente...")
        return []

    def filtrarAsignatura(self, asignatura: str) -> None:
        print(f"Filtrando horario del docente por la asignatura {asignatura}.")


class HorarioEstudiante(Horario):
    def __init__(self, dia: str, hora_inicio: float, hora_fin: float, periodo: str,
                 nivel: str, asignatura: str, paralelo: str, salon: str, docente: str, carrera: str):
        super().__init__(dia, hora_inicio, hora_fin, periodo, nivel, asignatura, paralelo)
        self.salon = salon
        self.docente = docente
        self.carrera = carrera

    def descargarHorarioPdf(self) -> None:
        print("Generando archivo PDF con la malla de horario del estudiante...")

    def verificarChoqueMateria((self) -> bool:
        print("Verificando consistencia de materias asignadas...")
        return False


class HorarioEstudianteBloque(HorarioEstudiante):
    def __init__(self, dia: str, hora_inicio: float, hora_fin: float, periodo: str,
                 nivel: str, asignatura: str, paralelo: str, salon: str, docente: str, carrera: str):
        super().__init__(dia, hora_inicio, hora_fin, periodo, nivel, asignatura, paralelo, salon, docente, carrera)


class HorarioEstudianteVariado(HorarioEstudiante):
    def __init__(self, dia: str, hora_inicio: float, hora_fin: float, periodo: str,
                 nivel: str, asignatura: str, paralelo: str, salon: str, docente: str, carrera: str,
                 tipo_matricula: str):
        super().__init__(dia, hora_inicio, hora_fin, periodo, nivel, asignatura, paralelo, salon, docente, carrera)
        self.tipo_matricula = tipo_matricula


class HorarioSalon(Horario):
    def consultarHorasLibres(self) -> List[str]:
        print("Consultando disponibilidad horaria del salón...")
        return []

    def bloquearSalonPorMantenimiento(self) -> None:
        print("El salón ha sido marcado en estado de mantenimiento.")


class Registro:
    def __init__(self, cedula_estudiante: int, codigo_de_registro: int, fecha_registro: int, estado: str):
        self.cedula_estudiante = cedula_estudiante
        self.codigo_de_registro = codigo_de_registro
        self.fecha_registro = fecha_registro
        self.estado = estado

    def registrarseHorario(self) -> None:
        print("Procesando registro en la materia...")

    def imprimirComprobante(self) -> None:
        print("Comprobante oficial impreso correctamente.")

    def imprimirMateriasRegistradas(self) -> None:
        print("Imprimiendo listado oficial de materias asignadas.")


class Asignatura:
    def __init__(self, nombre: str, nivel: int, carrera: str, codigo_de_materia: int):
        self.nombre = nombre
        self.nivel = nivel
        self.carrera = carrera
        self.codigo_de_materia = codigo_de_materia


class Carrera:
    def __init__(self, nombre: str, codigo: int):
        self.nombre = nombre
        self.codigo = codigo


class Facultad:
    def __init__(self, nombre: str, numero_de_facultad: int):
        self.nombre = nombre
        self.numero_de_facultad = numero_de_facultad


class Paralelo:
    def __init__(self, asignatura: str, paralelo: str, estudiantes: int):
        self.asignatura = asignatura
        self.paralelo = paralelo
        self.estudiantes = estudiantes


class PeriodoAcademico:
    def __init__(self, nombre: str, fecha_inicio: str, fecha_fin: str):
        self.nombre = nombre
        self.fecha_inicio = fecha_inicio
        self.fecha_fin = fecha_fin