from __future__ import annotations
from canvasapi import Canvas
import requests
from abc import ABC, abstractmethod
from enum import Enum
from proxy import Proxy, LocalDatabase

class Todo():
    '''Clase para construir un todo con formato de habitica'''
    def __init__(self, todo:dict):
        date = todo['date']
        self.id:int     = todo['id']
        self.name:str   = todo['text']
        self.due_at:str = date[0:len(date)-5]+date[len(date)-1] if (date is not None) else date

    def __str__(self)-> str:
        return f'{self.name} -> Due date: {self.due_at}'

class Homework():
    '''Clase para construir una tarea con formato de canva'''
    def __init__(self, homework:canvasapi.assignment.Assignment):
        self.id:int         = homework.id
        self.name:str       = homework.name
        self.due_at:str     = homework.due_at
        self.lock_at:str    = homework.lock_at
        self.status:Status  = Homework.Status.UNCHECKED

    class Status(Enum):
        # name        value  
        UNCHECKED   = 'Unchecked'
        UPDATE      = 'Update'
        ACTIVE      = 'Active'
        COMPLETED   = 'Completed'
        UPLOADED    = 'Uploaded'

    def __str__(self)-> str:
        return f'{self.name} -> Status: {self.status.value} | Due date: {self.due_at} | Lock date: {self.lock_at}'

class Course():
    '''Clase para construir un curso con formato de canva'''
    def __init__(self, course:canvasapi.course.Course):
        self.id:int             = course.id
        self.name:str           = course.name
        self.homework:list  = self.get_homework(course)

    def __str__(self)-> str:
        name_homework = '\n\t'.join(map(str, self.homework))
        return f'{self.name} \n\t{name_homework}'

    def get_homework(self, course:canvasapi.course.Course) -> list:
        ''' Retorna las tareas pendientes de un curso '''
        valid_homework = []
        for homework in course.get_assignments(bucket='future'):
            if homework.name != 'Roll Call Attendance':
                valid_homework.append(Homework(homework))
        return valid_homework

##################################################
# Productos Abstractos
##################################################
class User(ABC):
    '''Clase abstracta que construir una silla'''    
    def __init__(self, user:str, key:str):
        self.api_user:str   = user
        self.api_key:str    = key

##################################################
# Productos Concretos
##################################################
class UserCanva(User):
    ''' Clase abstracta para definir sillas con estilo moderno '''
    def __init__(self, local_database:Proxy):
        User.__init__(self, 
            local_database.obtener_sensitive_data(local_database.Parameter.CANVA_USER), 
            local_database.obtener_sensitive_data(local_database.Parameter.CANVA_KEY))
        self.id:int             = int(local_database.obtener_sensitive_data(local_database.Parameter.CANVA_USER_ID))
        self.current_term:int   = int(local_database.obtener_sensitive_data(local_database.Parameter.CANVA_TERM_ID))
        self.api:canvasapi.canvas.Canvas    = Canvas(self.api_user, self.api_key)
        self.user:canvasapi.user.User       = self.api.get_user(self.id)
        self.courses:list       = self.get_courses()

    def __str__(self)-> str:
        name_course = '\n'.join(map(str, self.courses))
        return f'{self.user.name} Canva\'s Profile \n{name_course}'

    def get_courses(self) -> list:
        ''' Retorna los cursos del semestre actual '''
        classes = []
        for course in self.user.get_courses(enrollment_state='active'): 
            if course.enrollment_term_id == self.current_term:
                classes.append(Course(course))
        return classes


class UserHabitica(User):
    '''Clase abstracta para definir sillas con estilo moderno'''
    def __init__(self, local_database:Proxy):
        User.__init__(self, 
            local_database.obtener_sensitive_data(local_database.Parameter.HABITICA_USER), 
            local_database.obtener_sensitive_data(local_database.Parameter.HABITICA_KEY))
        self.auth_headers:dict  = {'x-api-user': self.api_user, 'x-api-key': self.api_key}
        self.canva_tag_id:str   = self.get_canvas_tag_id()
        self.todos:dict         = self.get_current_todos()

    def __str__(self)-> str:
        todo = '\n\t'.join(map(str, self.todos.values()))
        return f'Habitica\'s Profile \n{todo}'

    def get_canvas_tag_id(self) -> str:
        ''' Retorna el id de 'Canvas' tag '''
        request = requests.get(
          'https://habitica.com/api/v3/tags',
          headers=self.auth_headers)
        assert request.status_code == 200
        for tag in request.json()['data']:
            if 'Canvas' == tag['name']:
                return tag['id']
        return ''

    def post_new_todo(self, task_json:set) -> int:
        ''' Retorna el status del posteo a habitica '''
        request = requests.post( 
          'https://habitica.com/api/v3/tasks/user',
          json=task_json,
          headers=self.auth_headers)
        assert request.status_code == 201, request.json()
        return request.status_code

    def put_todo(self, task_json:set, task_id:str) -> int:
        ''' Retorna el status de una actualizacion de habitica '''
        request = requests.put( 
          'https://habitica.com/api/v3/tasks/' + str(task_id),
          json=task_json,
          headers=self.auth_headers)
        assert request.status_code == 200, request.json()
        return request.status_code

    def get_current_todos(self) -> dict:
        ''' Retorna los todos de habitica con el id 'Canvas' '''
        request = requests.get(
          'https://habitica.com/api/v3/tasks/user?type=todos',
          headers=self.auth_headers)
        assert request.status_code == 200
        todos = {}
        for todo in request.json()['data']:
            if self.canva_tag_id in todo['tags']: 
                todos[todo['notes']] = Todo(todo)
        return todos

    def is_homework_on_habitica(self, homework_id:int) -> bool:
        ''' Retorna si una tarea de canva esta en habitica '''
        return str(homework_id.id) in self.todos.keys()

    def is_homework_due_at(self, homework:Homework) -> bool:
        ''' Retorna si una tarea de canva cambio de fecha respecto a la de habitica '''
        return homework.due_at != self.todos[str(homework.id)].due_at


##################################################
# Interfase de la fábrica
##################################################
class Canva2Habitica(ABC):
    @abstractmethod
    def populate_user_info(self, local_database:Proxy) -> None:
        '''crea un usuario de alguna plataforma'''
        pass

##################################################
# Fabricas concretas
##################################################
class Canva(Canva2Habitica):
  def populate_user_info(self, local_database:Proxy) -> UserCanva:
    '''crea un usuario de canva'''
    return UserCanva(local_database)

class Habitica(Canva2Habitica):
  def populate_user_info(self, local_database:Proxy) -> UserHabitica:
    '''crea un usuario de habitica'''
    return UserHabitica(local_database)
    
##################################################
# Clase Auxiliar para clientes
##################################################
class Client():

    class Plataform(Enum):
        # name        value  
        PROXY       = Proxy(LocalDatabase())
        HABITICA    = Habitica().populate_user_info(PROXY)
        CANVA       = Canva().populate_user_info(PROXY)

    def canva_processing(canva_homework:Homework) -> None:
        ''' dependiendo del estado de una tarea de canva, actualiza o sube su informacion a habitica '''
        task_json={ 
            "text": canva_homework.name, "type": "todo",
            "notes": canva_homework.id,  "priority": 2,  
            "tags": Client.Plataform.HABITICA.value.canva_tag_id, 
            "date":canva_homework.due_at
        }
        if Client.Plataform.HABITICA.value.is_homework_on_habitica(canva_homework):
            if Client.Plataform.HABITICA.value.is_homework_due_at(canva_homework):
                Client.Plataform.HABITICA.value.put_todo(task_json, Client.Plataform.HABITICA.value.todos[str(canva_homework.id)].id) 
                canva_homework.status = Homework.Status.UPDATE                
            else:
                canva_homework.status = Homework.Status.ACTIVE                
        else:
            if Client.Plataform.PROXY.value.in_uploaded_id(canva_homework.id):
                canva_homework.status = Homework.Status.COMPLETED                
        if canva_homework.status == Homework.Status.UNCHECKED:
            Client.Plataform.HABITICA.value.post_new_todo(task_json)
            Client.Plataform.PROXY.value.insertar_uploaded_id(canva_homework.id)
            canva_homework.status = Homework.Status.UPLOADED

    def upload_homework() -> None:
        ''' procesa cada una de las tareas de cada uno de los cursos de canva '''
        valid_homework = []
        list(map(lambda s: valid_homework.extend(s.homework), Client.Plataform.CANVA.value.courses))
        list(map(lambda s: Client.canva_processing(s), valid_homework))
        
    @staticmethod 
    def user(tipo: Plataform) -> Canva2Habitica:
        ''' Crea un nuevo usuario'''
        return tipo.value


if __name__ == '__main__':
    #Creamos cada uno de los usuarios
    canva = Client.user(Client.Plataform.CANVA)
    habitica = Client.user(Client.Plataform.HABITICA)

    #Procesamos las tareas de canva y las subimos a habitica
    Client.upload_homework()

    #Imprimimos la infomacion de cada tarea
    print(canva)
  
