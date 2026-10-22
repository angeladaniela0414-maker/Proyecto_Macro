class Horario1:
    #Atributo de clase 
    vigencia = "En proceso de aprobacion"

    def __init__(self, periodo, nivel):
        print (f"se ha creado el hoarrio del periodo {periodo} y del nivel {nivel}")
        self.__periodo = periodo
        self.nivel = nivel
    
    def mostrar (self, tipo):
        print (f"este es el horario {tipo}, del periodo {self.periodo} y del nivel {self.nivel} ")
        
    def generar (self, tipo):
        print (f"se ha generado el horario {tipo}, del periodo {self.periodo} y del nivel {self.nivel} ")
        
horario1 = Horario("2026-2", "Tercero")
print(type(horario1))
print(horario1.periodo)
print(horario1.nivel)
print(horario1.vigencia)
horario1.generar("Docente")
horario1.mostrar("Docente")

Horario.vigencia = "Aprobado"
print (horario1.vigencia)
horario2 = Horario("2026-2", "Cuarto")
print (horario2.vigencia)

horario1.vigencia = "Suspendido"
print (horario1.vigencia)
print (horario2.vigencia)
Horario.vigencia = "Caducado"
print (horario1.vigencia)
print (horario2.vigencia)

horario2.vigente = "Renovado"
print (horario1.vigencia)
print (horario2.vigencia)

Horario.vigencia = "Final  de la practica"
print (horario1.vigencia)
print (horario2.vigencia)

horario3 = Horario ("2026-2", "Quinto")
print (horario1.vigencia)
print (horario2.vigencia)
print (horario3.vigencia)


@properity
def  

#revisar la pagina aprende python

# los atributos de las clases solo cambia su intancia si especificamente se le da un  valor a ese objeto, 
#pero si a este nunca se le asigna un valor entonces si cambiara su valor por el de la clase 
#una propiedad me permite accedar como si fuera un atributo (actua como un geter)

#¿cuando debo utilizar un metodo y cuando una propiedadun?
# accion  un proceso es metodo 
#acceder  dato o ejecucion es una propiedad -.



