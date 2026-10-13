class Gestion_Academica:
    horas_administrativas = 120    
    def __init__(self, facultad, cargo, carrera):
        self.facultad = facultad
        self.cargo = cargo
        self.carrera= carrera

    def asignarHorario (self, horas_docente):
        return horas_docente <= self.horas_administrativas
    
    @classmethod
    def registroPermisos (cls, hora_limite):
        return cls.horas_adminsitracion <= hora_limite

    @staticmethod
    def rol (facultad, cargo, carrera):
        return f"{facultad.title()} {cargo.title()} {carrera.title()}"
        

class Docente:
    horas_max_semana = 40 # atributo de clase que yo asigno un valor 
    def __init__(self, cedula, nombre, apellido, especialidad, asignatura, nivel):
        self.cedula =cedula    #atributo de instancia no olvidar 
        self.nombre = nombre
        self.apellido = apellido
        self.especialidad = especialidad
        self.asignatura = asignatura 
        self.nivel = nivel
    
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


class Estudiante:
    nivel="cuarto"
    def __init__(self, codigo, nombre, apellido, correo, curso, nivel ):
        print(f"creamos al usuario del estudiante ,{nombre}, {apellido}")
        self.__codigo = codigo
        self.nombre = nombre 
        self.apellido = apellido
        self.correo = correo
        self.curso = curso
        self.nivel = nivel

    def consultar_nivel(self,nivel_actual):
        return nivel_actual == self.nivel 
    
    @classmethod
    def desde_texto(cls, texto):
        nombre, carrera, nivel = texto.split(",")
        return cls(nombre, carrera, int(nivel))
    
       
    @staticmethod
    def es_correo_institucional(correo):
        arroba="@universidad.edu.ec"  
        return correo.arroba


class Horario:
    
    def __init__(self, dia, hora_inicio, hora_fin, periodo, nivel):
        self.dia= dia
        self.hora_inicio = hora_inicio
        self.hora_fin = hora_fin
        self.periodo = periodo
        self.nivel = nivel
            
    def duracion(self):
        return self.hora_fin - self.hora_inicio

    @classmethod
    def cambiar_hora_limite(cls, nueva_hora):
        cls.hora_limite = nueva_hora

class Registro:
    def __init__(self, cedulaEstudiante , codigoDeRegistro, fechaaRegistro, estado):
        self.cedulaEstudiante = cedulaEstudiante
        self.codigoDeRegistro = codigoDeRegistro
        self.fechaaRegistro = fechaaRegistro
        self.estado = estado

