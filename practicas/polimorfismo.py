import abc 
class vehicle(metaclass=abc.ABCMeta):
    @abc.abstractmethod
    def start_engine(self):
        pass

    @abc.abstractmethod
    def stop_engine(self):
        pass


class ClaseAbstracta(metaclass=abc.ABCMeta):
    @abc.abstractmethod
    def metodo_abstracto(self):
        pass


from abc import ABC, abstractmethod
from abc import ABCMeta

class Mando(metaclass=ABCMeta):
    @abstractmethod
    def siguiente_canal(self):
        pass

    @abstractmethod
    def canal_anterior(self):
        pass

    @abstractmethod
    def subir_volumen(self):
        pass

    @abstractmethod
    def bajar_volumen(self):
        pass

    from abc impot ABC, abstractmethod
     