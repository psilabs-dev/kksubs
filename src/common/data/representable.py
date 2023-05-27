from abc import ABC, abstractclassmethod
from typing import Dict

class RepresentableData(ABC):

    def __repr__(self) -> str:
        return str(self.__dict__)

    def __eq__(self, __value: object) -> bool:
        if __value is None:
            return False
        return self.__dict__ == __value.__dict__
    
    @abstractclassmethod
    def deserialize(self, data) -> "RepresentableData":
        ...

    def serialize(self) -> Dict:
        attributes = {}
        for attribute, value in self.__dict__.items():
            if isinstance(value, RepresentableData):
                attributes[attribute] = value.serialize()
            else:
                attributes[attribute] = value
        return attributes