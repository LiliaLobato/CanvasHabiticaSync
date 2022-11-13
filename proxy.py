from abc import ABC, abstractmethod
from enum import Enum

# -----------------------------------------------------------------------------
# Singleto auxiliar
# -----------------------------------------------------------------------------
def singleton(clase):
    ''' singleton auxiliar para la proxy '''
    instancias = {}
    def obtener_instancia(*args, **kwargs):
        if clase not in instancias:
            instancias[clase] = clase(*args, **kwargs)
        return instancias[clase]
    return obtener_instancia

# -----------------------------------------------------------------------------
# 1.- Service Interface
# -----------------------------------------------------------------------------
class Operaciones(ABC):
    @abstractmethod
    def obtener_sensitive_data(self, line_num:int) -> str:
        ''' Retorna un parametro de informacion sensitiva '''
        pass

    @abstractmethod
    def obtener_uploaded_id(self) -> str:
        ''' Retorna el historial de id subidos a Habitica '''
        pass

    @abstractmethod
    def insertar_uploaded_id(self, id:str) -> str:
        ''' Inserta un id al historial de Habitica '''
        pass

# -----------------------------------------------------------------------------
# 2.- Service
# -----------------------------------------------------------------------------
@singleton
class LocalDatabase(Operaciones):

    def __init__(self):
        self.__sensitive_data:list = self.llenar_datos("sensitive_data.txt")
        self.__uploaded_id:list = self.llenar_datos("uploaded_id.txt")

    def obtener_sensitive_data(self, line_num:int) -> str:
        ''' Retorna un parametro de informacion sensitiva '''
        return self.__sensitive_data[line_num]

    def obtener_uploaded_id(self) -> str:
        ''' Retorna el historial de id subidos a Habitica '''
        return self.__uploaded_id

    def llenar_datos(self, file:str) -> list:
        ''' Retorna los elementos escritos en un documento '''
        with open(str(file)) as f:
            return list(map(lambda s: s.rstrip("\n"), f.readlines()))

    def insertar_uploaded_id(self, id:int) -> None:
        ''' Inserta un id al historial de Habitica '''
        f = open("uploaded_id.txt", "a")
        f.write(str(id)+'\n')
        f.close()
        self.__uploaded_id = self.llenar_datos("uploaded_id.txt")

# -----------------------------------------------------------------------------
# 3.- Proxy
# -----------------------------------------------------------------------------
class Proxy(Operaciones):
    def __init__(self, db: LocalDatabase) -> None:
        self.__db:LocalDatabase = db

    class Parameter(Enum):
        # name      
        CANVA_USER      = 0
        CANVA_KEY       = 1
        CANVA_USER_ID   = 2
        CANVA_TERM_ID   = 3
        HABITICA_USER   = 5
        HABITICA_KEY    = 6    

    def obtener_sensitive_data(self, par:Parameter) -> str:
        ''' Retorna un parametro especifico de data sensitiva '''
        return self.__db.obtener_sensitive_data(par.value)

    def obtener_uploaded_id(self) -> str:
        ''' Retorna el historial de id subidos a Habitica '''
        return self.__db.obtener_uploaded_id()

    def insertar_uploaded_id(self, id:id) -> None:
        ''' Inserta un id al historial de Habitica '''
        self.__db.insertar_uploaded_id(id)

    def in_uploaded_id(self, id:id) -> bool:
        ''' Retorna si un id esta en el historial de Habitica '''
        return id in self.__db.obtener_uploaded_id()