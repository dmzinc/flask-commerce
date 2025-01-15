from abc import ABC, abstractmethod

class ConcreteProduct:
    pass

class Creator(ABC):
    @abstractmethod
    def factory_method(self):
        pass

    def some_operation(self):
        product = self.factory_method()
        return f"Creator: {product.operation()}"

class ConcreteCreator(Creator):
    def factory_method(self):
        return ConcreteProduct()
    

class DocumentCreator(ABC):
    @abstractmethod
    def create_document(self, file_path):
        pass

class PDFCreator(DocumentCreator):
    def create_document(self, file_path):
        return PDFDocument(file_path)

class WordCreator(DocumentCreator):
    def create_document(self, file_path):
        return WordDocument(file_path)
    

# class Document:
#     pass
# class WordDocument(Document):
#     pass
# class PDFDocument(Document):
#     pass

class Computer:
    def __init__(self):
        self.parts = []




class ComputerBuilder:
    def __init__(self):
        self.computer = Computer()

    def add_cpu(self, cpu):
        self.computer.parts.append(f"CPU: {cpu}")
        return self

    def add_memory(self, memory):
        self.computer.parts.append(f"Memory: {memory}")
        return self

    def build(self):
        return self.computer

# Usage
computer = ComputerBuilder().add_cpu("Intel i7").add_memory("32GB").build()


def singleton(class_):
    instances = {}
    def getinstance(*args, **kwargs):
        if class_ not in instances:
            instances[class_] = class_(*args, **kwargs)
        return instances[class_]
    return getinstance

class User:
    def __init__(self, name, id = '', email=''):
        self.name = name
        self.id = id
        self.email = email

    def to_dict(self):
        return {"name": self.name, 'id': self.id, 'email': self.email}
    
print(User('Matthew').to_dict())
print(User('Kenneth').to_dict())


class Service:
    space_required = 16
    def work(self):
        print("Service is doing something")

class Hardware:
    ram = 32

class Client:
    def __init__(self):
        self.service = None
        self.hardware = None
        self.allocation = 0

    def set_service(self, service: Service):
        self.service = service
    def set_hardware(self, hardware: Hardware):
        self.hardware = hardware
        self.allocation = self.hardware.ram

    def perform_task(self):
        
        self.service.work()

# Dependency Injection
service = Service()
client = Client()
client.set_service(service)
client.perform_task()

