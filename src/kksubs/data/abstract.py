from abc import abstractclassmethod, abstractmethod

from common.data.representable import RepresentableData

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