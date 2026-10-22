"""
Práctica: Programación orientada a objetos
Proyecto de aula: Sistema de Gestión Académica (horarios)

Clases: Docente, Estudiante, Asignatura, Salon, Horario
Cada clase tiene:
  - 3 atributos de instancia
  - 1 atributo de clase
  - 3 métodos: uno de instancia, uno de clase (@classmethod) y uno estático (@staticmethod)
"""


# ---------------------------------------------------------------
# 1. DOCENTE
# ---------------------------------------------------------------
class Docente:
    horas_max_semana = 20  # atributo de clase

    def __init__(self, nombre, apellido, especialidad):
        self.nombre = nombre                # atributos de instancia
        self.apellido = apellido
        self.especialidad = especialidad

    # Método de instancia (recibe un dato)
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


# ---------------------------------------------------------------
# 2. ESTUDIANTE
# ---------------------------------------------------------------
class Estudiante:
    nivel_maximo = 9  # atributo de clase

    def __init__(self, nombre, carrera, nivel):
        self.nombre = nombre                # atributos de instancia
        self.carrera = carrera
        self.nivel = nivel

    # Método de instancia
    def subir_nivel(self):
        if self.nivel < self.nivel_maximo:
            self.nivel += 1
            return f"{self.nombre} ahora está en nivel {self.nivel}"
        return f"{self.nombre} ya está en el último nivel ({self.nivel_maximo})"

    # Método de clase: crea un Estudiante desde un texto "nombre,carrera,nivel"
    @classmethod
    def desde_texto(cls, texto):
        nombre, carrera, nivel = texto.split(",")
        return cls(nombre, carrera, int(nivel))

    # Método estático (recibe un dato)
    @staticmethod
    def es_correo_institucional(correo):
        return correo.endswith("@universidad.edu.ec")


# ---------------------------------------------------------------
# 3. ASIGNATURA
# ---------------------------------------------------------------
class Asignatura:
    nota_minima = 7.0  # atributo de clase

    def __init__(self, nombre, nivel, creditos):
        self.nombre = nombre                # atributos de instancia
        self.nivel = nivel
        self.creditos = creditos

    # Método de instancia (recibe un dato)
    def aprueba(self, nota):
        return nota >= self.nota_minima

    # Método de clase
    @classmethod
    def cambiar_nota_minima(cls, nueva_nota):
        cls.nota_minima = nueva_nota

    # Método estático
    @staticmethod
    def horas_por_creditos(creditos):
        return creditos * 16


# ---------------------------------------------------------------
# 4. SALON
# ---------------------------------------------------------------
class Salon:
    capacidad_maxima = 40  # atributo de clase

    def __init__(self, numero, capacidad, estado="disponible"):
        self.numero = numero                # atributos de instancia
        self.capacidad = capacidad
        self.estado = estado

    # Método de instancia (recibe un dato)
    def puede_recibir(self, cantidad_estudiantes):
        return (self.estado == "disponible"
                and cantidad_estudiantes <= min(self.capacidad, self.capacidad_maxima))

    # Método de clase
    @classmethod
    def ajustar_capacidad_maxima(cls, nueva_capacidad):
        cls.capacidad_maxima = nueva_capacidad

    # Método estático
    @staticmethod
    def es_capacidad_valida(capacidad):
        return capacidad > 0


# ---------------------------------------------------------------
# 5. HORARIO
# ---------------------------------------------------------------
class Horario:
    hora_limite = 22  # atributo de clase (ninguna clase puede terminar después)

    def __init__(self, dia, hora_inicio, hora_fin):
        self.dia = dia                      # atributos de instancia
        self.hora_inicio = hora_inicio
        self.hora_fin = hora_fin

    # Método de instancia
    def duracion(self):
        return self.hora_fin - self.hora_inicio

    # Método de clase
    @classmethod
    def cambiar_hora_limite(cls, nueva_hora):
        cls.hora_limite = nueva_hora

    # Método estático (recibe datos): detecta cruce de horarios
    @staticmethod
    def se_cruzan(inicio1, fin1, inicio2, fin2):
        return inicio1 < fin2 and inicio2 < fin1

    def es_valido(self):
        return self.hora_fin <= self.hora_limite and self.duracion() > 0


# ===============================================================
# EJEMPLOS DE USO
# ===============================================================
if __name__ == "__main__":

    print("=== EJEMPLOS DE USO ===\n")

    # --- Docente ---
    d1 = Docente("carlos", "mendoza", "Programación")
    print("Docente:", Docente.nombre_completo(d1.nombre, d1.apellido))
    print("¿Puede tomar 18 horas?", d1.puede_tomar_horas(18))

    # --- Estudiante ---
    e1 = Estudiante("Ana Lopez", "Software", 3)
    e2 = Estudiante.desde_texto("Luis Vera,Software,9")
    print("\n" + e1.subir_nivel())
    print(e2.subir_nivel())
    print("¿Correo válido?", Estudiante.es_correo_institucional("ana@universidad.edu.ec"))

    # --- Asignatura ---
    a1 = Asignatura("Lógica de Programación", 1, 4)
    a2 = Asignatura("Bases de Datos", 3, 5)
    print("\n¿Aprueba con 7.5 en", a1.nombre + "?", a1.aprueba(7.5))
    print("Horas de", a2.nombre + ":", Asignatura.horas_por_creditos(a2.creditos))

    # --- Salon ---
    s1 = Salon(101, 35)
    s2 = Salon(202, 50)
    print("\nSalón 101 recibe 30:", s1.puede_recibir(30))
    print("Salón 202 recibe 45:", s2.puede_recibir(45))
    print("¿Capacidad 0 válida?", Salon.es_capacidad_valida(0))

    # --- Horario ---
    h1 = Horario("Lunes", 8, 10)
    h2 = Horario("Lunes", 9, 11)
    print("\nDuración h1:", h1.duracion(), "horas")
    print("¿h1 y h2 se cruzan?",
          Horario.se_cruzan(h1.hora_inicio, h1.hora_fin, h2.hora_inicio, h2.hora_fin))

    # ===========================================================
    # ATRIBUTO DE CLASE: cambios que afectan objetos ya creados
    # ===========================================================
    print("\n=== CAMBIO DEL ATRIBUTO DE CLASE (nota_minima) ===")
    print("Antes  -> a1 aprueba con 7.5:", a1.aprueba(7.5), "| a2 aprueba con 7.5:", a2.aprueba(7.5))

    # a1 y a2 ya existían; al cambiar el atributo de la clase, ambos se ven afectados
    Asignatura.cambiar_nota_minima(8.0)
    print("Después-> a1 aprueba con 7.5:", a1.aprueba(7.5), "| a2 aprueba con 7.5:", a2.aprueba(7.5))
    print("nota_minima vista desde a1:", a1.nota_minima, "| desde a2:", a2.nota_minima)

    # Un objeto nuevo también usa el valor actualizado
    a3 = Asignatura("Redes", 4, 4)
    print("Objeto nuevo a3 -> nota_minima:", a3.nota_minima)

    # Si se asigna el atributo desde una INSTANCIA, se crea uno propio y ya no sigue a la clase
    a2.nota_minima = 6.0
    Asignatura.cambiar_nota_minima(9.0)
    print("\nTras dar a a2 su propia nota_minima y cambiar la clase a 9.0:")
    print("a1:", a1.nota_minima, "| a2:", a2.nota_minima, "| a3:", a3.nota_minima)

    # Otro ejemplo rápido con Salon
    print("\n=== CAMBIO DE Salon.capacidad_maxima ===")
    print("Antes  -> s2 recibe 45:", s2.puede_recibir(45))
    Salon.ajustar_capacidad_maxima(60)
    print("Después-> s2 recibe 45:", s2.puede_recibir(45))
