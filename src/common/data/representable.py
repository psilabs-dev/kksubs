from abc import ABC, abstractclassmethod, abstractmethod

class RepresentableData(ABC):

    def __repr__(self) -> str:
        return str(self.__dict__)

    def __eq__(self, __value: object) -> bool:
        if __value is None:
            return False
        return self.__dict__ == __value.__dict__