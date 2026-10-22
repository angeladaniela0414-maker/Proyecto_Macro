# Tarea.py

class Tarea:

    def __init__(self, nombre, estado):
        self.__nombre = nombre
        self.__estado = estado

    # SETTERS
    def setNombre(self, nombre):
        self.__nombre = nombre

    def setEstado(self, estado):
        self.__estado = estado

    # GETTERS
    def getNombre(self):
        return self.__nombre

    def getEstado(self):
        return self.__estado

    def __str__(self):
        estado_texto = "completada" if self.__estado else "pendiente"
        return f"Tarea = {self.__nombre}, estado={estado_texto}"