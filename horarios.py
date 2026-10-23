from abc import ABCMeta, abstractmethod


class Materia:
    def __init__(self, codigo, nombre, semestre, area, tipo_salon="Aula"):
        self.codigo = codigo
        self.nombre = nombre
        self.semestre = semestre
        self.area = area
        self.tipo_salon = tipo_salon

    @property
    def horas_total(self):
        return self.acd + self.ape + self.aa

    def __str__(self):
        return f"{self.codigo} {self.nombre}"


class Profesor:
    def __init__(self, id_profesor, nombre, materias=None, max_horas_semana=20):
        self.id_profesor = id_profesor
        self.nombre = nombre
        self.materias = materias if materias is not None else []   
        self.max_horas_semana = max_horas_semana

    def puede_dictar(self, materia):
        return materia.codigo in self.materias

    def __str__(self):
        return self.nombre


class Salon:
    def __init__(self, id_salon, nombre, capacidad=30, tipo_salon="Aula", disponibilidad=True):
        self.id_salon = id_salon
        self.nombre = nombre
        self.capacidad = capacidad
        self.tipo_salon = tipo_salon
        self.disponibilidad = disponibilidad

    def __str__(self):
        return f"{self.nombre} ({self.tipo_salon}, capacidad {self.capacidad})"


class Bloque_horario:
    """Una sesión de clase: una materia, de un paralelo, con un profesor, en un salón."""
    def __init__(self, dia, hora_inicio, hora_fin, salon, materia, profesor, paralelo):
        self.dia = dia
        self.hora_inicio = hora_inicio
        self.hora_fin = hora_fin
        self.salon = salon
        self.materia = materia
        self.profesor = profesor
        self.paralelo = paralelo        

    def horas(self):
        h1, m1 = map(int, self.hora_inicio.split(":"))
        h2, m2 = map(int, self.hora_fin.split(":"))
        return ((h2 * 60 + m2) - (h1 * 60 + m1)) / 60

    def se_cruza_con(self, otro):
        return (self.dia == otro.dia
                and self.hora_inicio < otro.hora_fin
                and otro.hora_inicio < self.hora_fin)

    def tiene_conflicto_con(self, otro):
        return self.se_cruza_con(otro) and (
            self.profesor.id_profesor == otro.profesor.id_profesor
            or self.paralelo == otro.paralelo
            or self.salon.id_salon == otro.salon.id_salon
        )

    def __str__(self):
        return (f"{self.dia} {self.hora_inicio}-{self.hora_fin} | {self.paralelo} | "
                f"{self.materia.nombre} | {self.profesor.nombre} | {self.salon.nombre}")



class Horario(metaclass=ABCMeta):
    def __init__(self, id_horario, periodo_academico, bloques, **kwargs):
        super().__init__(**kwargs)
        self.id_horario = id_horario
        self.periodo_academico = periodo_academico
        self.bloques = bloques

    @abstractmethod
    def consultar_horario(self):
        pass


class Horario_estudiante(Horario):          
    def __init__(self, id_horario, periodo_academico, paralelo, **kwargs):
        super().__init__(id_horario, periodo_academico, **kwargs)
        self.paralelo = paralelo

    def consultar_horario(self):
        return [b for b in self.bloques if b.paralelo == self.paralelo]


class Horario_semestre(Horario):
    def __init__(self, id_horario, periodo_academico, semestre, **kwargs):
        super().__init__(id_horario, periodo_academico, **kwargs)
        self.semestre = semestre

    def consultar_horario(self):
        return [b for b in self.bloques if b.materia.semestre == self.semestre]


class Horario_profesor(Horario):
    def __init__(self, id_horario, periodo_academico, profesor, **kwargs):
        super().__init__(id_horario, periodo_academico, **kwargs)
        self.profesor = profesor

    def consultar_horario(self):
        return [b for b in self.bloques if b.profesor.id_profesor == self.profesor.id_profesor]


class Horario_salon(Horario):
    def __init__(self, id_horario, periodo_academico, salon, **kwargs):
        super().__init__(id_horario, periodo_academico, **kwargs)
        self.salon = salon

    def consultar_horario(self):
        return [b for b in self.bloques if b.salon.id_salon == self.salon.id_salon]
