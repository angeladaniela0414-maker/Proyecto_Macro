from abc import ABCMeta
from abc import abstractmethod

class Asignatura:
    def __init__(self, id_asignatura, nombre, semestre):
        self.id_asignatura = id_asignatura
        self.nombre = nombre
        self.semestre = semestre

    def __str__(self):
        return f"{self.nombre} - Semestre {self.semestre}"
    
class Salon:
    def __init__(self, id_salon, nombre, capacidad=30, tipo_salon="Aula", disponibilidad=True):
        self.id_salon = id_salon
        self.nombre = nombre
        self.capacidad = capacidad
        self.tipo_salon = tipo_salon
        self.disponibilidad = disponibilidad

class Bloque_horario:
    def __init__(self, dia, hora_inicio, hora_fin, salon, asignatura, profesor, paralelo):
        self.dia = dia
        self.hora_inicio = hora_inicio
        self.hora_fin = hora_fin
        self.salon = salon
        self.asignatura = asignatura
        self.profesor = profesor
        self.paralelo = paralelo

    def se_cruza_con(self, otro_bloque): #otro representa un objeto de tipo Bloque_Horario

        mismo_dia = self.dia == otro_bloque.dia

        horas_cruzadas = (
            self.hora_inicio < otro_bloque.hora_fin
            and otro_bloque.hora_inicio < self.hora_fin
        )

        return mismo_dia and horas_cruzadas

    def __str__(self):
        return (
            f"{self.dia}: {self.hora_inicio}-{self.hora_fin} | "
            f"{self.asignatura.nombre} | "
            f"Profesor: {self.profesor} | "
            f"Paralelo: {self.paralelo} | "
            f"Salón: {self.salon.nombre}"
        )


#clase abstracta horario
class Horario(metaclass=ABCMeta):
    def __init__(self, id_horario, periodo_academico, **kwargs):
        super().__init__(**kwargs)
        self.id_horario = id_horario
        self.periodo_academico = periodo_academico
        self.bloques = [] #sesion

    def agregar_bloque(self, bloque):
        if self.validar_cruce_horario(bloque):
            print("No se puede agregar: existe un cruce.")
            return False

        self.bloques.append(bloque)
        return True

    def existe_conflicto(self, nuevo, existente):
        if not nuevo.se_cruza_con(existente):
            return False

        mismo_profesor = (
            nuevo.profesor == existente.profesor
        )
        mismo_paralelo = (
            nuevo.paralelo == existente.paralelo
        )
        mismo_salon = (
            nuevo.salon.id_salon == existente.salon.id_salon
        )

        return (
            mismo_profesor
            or mismo_paralelo
            or mismo_salon
        )

    

    @abstractmethod
    def consultar_horario(self):
        pass

 

    @abstractmethod
    def validar_cruce_horario(self, otro_bloque):
        pass

class Horario_profesor(Horario):
    def __init__(self, id_horario, periodo_academico, profesor=None, **kwargs):
        super().__init__(id_horario, periodo_academico, **kwargs)
        self.profesor = profesor

    def consultar_horario(self):
        for bloque in self.bloques:
            if bloque.profesor == self.profesor:
                print(bloque)

  
    def validar_cruce_horario(self, nuevo_bloque):
        for bloque in self.bloques:
            if bloque.profesor == self.profesor:
                if self.existe_conflicto(nuevo_bloque, bloque):
                    return True
        return False


class Horario_estudiante(Horario):
    def __init__(self, id_horario, periodo_academico, estudiante=None, **kwargs):
        super().__init__(id_horario, periodo_academico, **kwargs)
        self.estudiante = estudiante

    def consultar_horario(self):
        for bloque in self.bloques:
            if bloque.paralelo == self.estudiante:
                print(bloque)



    def validar_cruce_horario(self, nuevo_bloque):
        for bloque in self.bloques:
            if self.existe_conflicto(nuevo_bloque, bloque):
                return True
        return False

class Horario_catedra(Horario_estudiante, Horario_profesor):
    def __init__(self, id_horario, periodo_academico, profesor, estudiante):
        super().__init__(
            id_horario,
            periodo_academico,
            profesor=profesor,
            estudiante=estudiante
        )

    def consultar_horario(self):
        return [
            b for b in self.bloques
            if b.profesor == self.profesor
            and b.paralelo == self.estudiante
        ]
    
class Horario_salon(Horario):
    def __init__(self, id_horario, periodo_academico, salon):
        super().__init__(id_horario, periodo_academico)
        self.salon = salon

    def consultar_horario(self):
        for bloque in self.bloques:
            if bloque.salon.id_salon == self.salon.id_salon:
                print(bloque)


    def validar_cruce_horario(self, nuevo_bloque):
        for bloque in self.bloques:
            if self.existe_conflicto(nuevo_bloque, bloque):
                return True
        return False
