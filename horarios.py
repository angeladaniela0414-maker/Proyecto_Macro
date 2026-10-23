from abc import ABCMeta, abstractmethod

class Materia:
    def __init__(self, codigo, nombre, semestre, area, tipo_salon='Aula', horas_semana=3):
        self.codigo = codigo
        self.nombre = nombre
        self.semestre = semestre
        self.area = area
        self.tipo_salon = tipo_salon
        self.horas_semana = horas_semana

    def __str__(self):
        return f'{self.codigo} {self.nombre}'

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
    def __init__(self, id_salon, nombre, capacidad=30, tipo_salon='Aula', disponibilidad=True):
        self.id_salon = id_salon
        self.nombre = nombre
        self.capacidad = capacidad
        self.tipo_salon = tipo_salon
        self.disponibilidad = disponibilidad

    def __str__(self):
        return f'{self.nombre} ({self.tipo_salon}, capacidad {self.capacidad})'

class Bloque_horario:
    def __init__(self, dia, hora_inicio, hora_fin, salon, materia, profesor, paralelo):
        self.dia = dia
        self.hora_inicio = hora_inicio
        self.hora_fin = hora_fin
        self.salon = salon
        self.materia = materia
        self.profesor = profesor
        self.paralelo = paralelo  # texto: '1A', '2B', etc.

    def horas(self):
        h1, m1 = map(int, self.hora_inicio.split(':'))
        h2, m2 = map(int, self.hora_fin.split(':'))
        return ((h2 * 60 + m2) - (h1 * 60 + m1)) / 60

    def se_cruza_con(self, otro):
        return (self.dia == otro.dia and self.hora_inicio < otro.hora_fin
                and otro.hora_inicio < self.hora_fin)

    def tiene_conflicto_con(self, otro):
        if not self.se_cruza_con(otro):
            return False
        if self.profesor.id_profesor == otro.profesor.id_profesor:
            return True
        if self.paralelo == otro.paralelo:
            return True
        if self.salon is not None and otro.salon is not None:
            if self.salon.id_salon == otro.salon.id_salon:
                return True
        return False

    def __str__(self):
        salon = self.salon.nombre if self.salon is not None else 'Virtual'
        return (f'{self.dia} {self.hora_inicio}-{self.hora_fin} | {self.paralelo} | '
                f'{self.materia.nombre} | {self.profesor.nombre} | {salon}')

class Horario(metaclass=ABCMeta):
    def __init__(self, id_horario, periodo_academico, bloques):
        self.id_horario = id_horario
        self.periodo_academico = periodo_academico
        self.bloques = bloques

    @abstractmethod
    def consultar_horario(self):
        pass

    def imprimir_horario(self):
        encontrados = self.consultar_horario()
        if not encontrados:
            print('No hay horarios para esta consulta.')
            return
        for bloque in encontrados:
            print(bloque)

class Horario_estudiante(Horario):
    def __init__(self, id_horario, periodo_academico, bloques, paralelo):
        super().__init__(id_horario, periodo_academico, bloques)
        self.paralelo = paralelo

    def consultar_horario(self):
        resultado = []
        for b in self.bloques:
            if b.paralelo == self.paralelo:
                resultado.append(b)
        return resultado

class Horario_semestre(Horario):
    def __init__(self, id_horario, periodo_academico, bloques, semestre):
        super().__init__(id_horario, periodo_academico, bloques)
        self.semestre = semestre

    def consultar_horario(self):
        resultado = []
        for b in self.bloques:
            if b.materia.semestre == self.semestre:
                resultado.append(b)
        return resultado

class Horario_profesor(Horario):
    def __init__(self, id_horario, periodo_academico, bloques, profesor):
        super().__init__(id_horario, periodo_academico, bloques)
        self.profesor = profesor

    def consultar_horario(self):
        resultado = []
        for b in self.bloques:
            if b.profesor.id_profesor == self.profesor.id_profesor:
                resultado.append(b)
        return resultado

class Horario_salon(Horario):
    def __init__(self, id_horario, periodo_academico, bloques, salon):
        super().__init__(id_horario, periodo_academico, bloques)
        self.salon = salon

    def consultar_horario(self):
        resultado = []
        for b in self.bloques:
            if b.salon is not None and b.salon.id_salon == self.salon.id_salon:
                resultado.append(b)
        return resultado
