from abc import ABC, abstractclassmethod, abstractmethod

class RepresentableData(ABC):

    def __repr__(self) -> str:
        return str(self.__dict__)

    def __eq__(self, __value: object) -> bool:
        if __value is None:
            return False
        return self.__dict__ == __value.__dict__

class BaseData(RepresentableData):
    field_name:str

    @abstractclassmethod
    def get_default(cls):
        ...

    @abstractclassmethod
    def from_dict(cls, style_dict):
        ...
    
    @abstractmethod
    def coalesce(self, other):
        ...

    @abstractmethod
    def correct_values(self):
        ...

    def corrected(self):
        self.correct_values()
        return self
    
    pass