from abc import ABC, abstractclassmethod, abstractmethod
import logging
from PIL import ImageColor
from typing import List, Optional

# object ops
def coalesce(*args):
    for arg in args:
        if arg is not None:
            return arg
    return None

logger = logging.getLogger(__name__)

def to_validated_value(value, values):
    if value is None or value in values:
        return value
    raise ValueError(value)

def to_integer(value) -> Optional[int]:
    if value is None or isinstance(value, int):
        return value
    if isinstance(value, str):
        return int(value)
    raise TypeError(type(value))

def to_float(value) -> Optional[float]:
    if value is None or isinstance(value, (float, int)):
        return value
    if isinstance(value, str):
        return float(value)
    raise TypeError(type(value))
    
def to_rgb_color(color):
    if color is None or isinstance(color, tuple):
        return color
    if (color[0]=="(" and color[-1]==")") or (color[0]=="[" and color[-1]=="]"):
        str_data = color[1:-1]
        return tuple(map(int, str_data.split(",")))
    if isinstance(color, list):
        return (color[0], color[1], color[2])
    else:
        return ImageColor.getrgb(color)
    
def to_xy_coords(value) -> Optional[tuple]:
    if value is None or isinstance(value, tuple):
        return value
    if isinstance(value, tuple):
        pass
    if isinstance(value, str):
        return tuple(map(int, value[1:-1].split(",")))
    if isinstance(value, list):
        return (int(value[0]), int(value[1]))
    raise TypeError(f"Coords has invalid type: {value} is of type {type(value)}.")

class BaseData(ABC):
    field_name:str

    def __repr__(self) -> str:
        return str(self.__dict__)
    def __eq__(self, __value: object) -> bool:
        if __value is None:
            return False
        return self.__dict__ == __value.__dict__
    
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

class TextData(BaseData):
    field_name = "text_data"

    def __init__(
            self, 
            font=None, 
            size=None, color=None, 
            stroke_size=None, stroke_color=None
    ):
        self.font = font
        self.size = size
        self.color = color
        self.stroke_size = stroke_size
        self.stroke_color = stroke_color
        pass

    @classmethod
    def get_default(cls):
        return TextData(
            font="default", 
            size=60, color="white",
            stroke_size=0, stroke_color=(0, 0, 0),
        )

    @classmethod
    def from_dict(cls, text_style_dict=None):
        if text_style_dict is None:
            return TextData()
        return TextData(**text_style_dict)
    
    def coalesce(self, other:"TextData"):
        if other is None:
            return
        self.font = coalesce(self.font, other.font)
        self.size = coalesce(self.size, other.size)
        self.color = coalesce(self.color, other.color)
        self.stroke_size = coalesce(self.stroke_size, other.stroke_size)
        self.stroke_color = coalesce(self.stroke_color, other.stroke_color)

    def correct_values(self):
        if self.font is not None:
            assert(isinstance(self.font, str))

        self.size = to_integer(self.size)
        self.color = to_rgb_color(self.color)
        self.stroke_size = to_integer(self.stroke_size)
        self.stroke_color = to_rgb_color(self.stroke_color)

    pass

class OutlineData(BaseData):
    field_name = "outline_data"

    def __init__(
            self,
            color=None, size=None, blur=None,
    ):
        self.color = color
        self.size = size
        self.blur = blur
        pass

    @classmethod
    def get_default(cls):
        return OutlineData(
            color="yellow",
            size=5,
            blur=0,
        )
    
    @classmethod
    def from_dict(cls, outline_dict=None):
        if outline_dict is None:
            return None
        return OutlineData(**outline_dict)
    
    def coalesce(self, other:"OutlineData"):
        if other is None:
            return
        self.color = coalesce(self.color, other.color)
        self.size = coalesce(self.size, other.size)
        self.blur = coalesce(self.blur, other.blur)

    def correct_values(self):
        self.color = to_rgb_color(self.color)
        self.size = to_integer(self.size)
        self.blur = to_integer(self.blur)

class BoxData(BaseData):
    field_name = "box_data"

    def __init__(
            self, 
            align_h=None, align_v=None, 
            box_width=None, 
            anchor=None,
            grid4=None,
            nudge=None,
    ):
        self.align_h = align_h
        self.align_v = align_v
        self.box_width = box_width
        self.anchor = anchor
        self.grid4 = grid4
        self.nudge = nudge
        pass

    @classmethod
    def get_default(cls):
        return BoxData(
            align_h="center", align_v="center",
            box_width=30,
            anchor=(0, 0),
        )

    @classmethod
    def from_dict(cls, box_style_dict=None):
        if box_style_dict is None:
            return BoxData()
        return BoxData(**box_style_dict)
    
    def coalesce(self, other:"BoxData"):
        if other is None:
            return
        self.align_h = coalesce(self.align_h, other.align_h)
        self.align_v = coalesce(self.align_v, other.align_v)
        self.box_width = coalesce(self.box_width, other.box_width)

        if self.anchor is None and self.grid4 is None:
            self.anchor = other.anchor
            self.grid4 = other.grid4

        self.nudge = coalesce(self.nudge, other.nudge)

    def correct_values(self):
        self.align_h = to_validated_value(self.align_h, {"left", "right", "center"})
        self.align_v = to_validated_value(self.align_v, {"bottom", "top", "center"})
        self.box_width = to_integer(self.box_width)
        self.anchor = to_xy_coords(self.anchor)
        self.grid4 = to_xy_coords(self.grid4)
        self.nudge = to_xy_coords(self.nudge)

class Style(BaseData):
    field_name = "style"

    def __init__(
            self, 
            style_id:str=None, 
            text_data:TextData=None,
            outline_data:OutlineData=None,
            box_data:BoxData=None,
    ):
        self.style_id = style_id
        self.text_data = text_data
        self.outline_data = outline_data
        self.box_data = box_data
        pass

    @classmethod
    def get_default(cls):
        return Style(
            style_id="",
            text_data=TextData.get_default(),
            # stroke_data=StrokeData.get_default(),
            box_data=BoxData.get_default(),
        )

    @classmethod
    def from_dict(cls, style_dict:dict=None):
        if style_dict is None:
            return Style()
        return Style(
            style_id=style_dict.get("style_id"),
            text_data=TextData.from_dict(text_style_dict=style_dict.get(TextData.field_name)),
            outline_data=OutlineData.from_dict(outline_dict=style_dict.get(OutlineData.field_name)),
            box_data=BoxData.from_dict(box_style_dict=style_dict.get(BoxData.field_name))
        )
    
    def coalesce(self, other:"Style"):
        if other is None:
            return
        self.style_id = coalesce(self.style_id, other.style_id)
        if self.text_data is None:
            self.text_data = other.text_data
        else:
            self.text_data.coalesce(other.text_data)
        if self.outline_data is None:
            self.outline_data = other.outline_data
        else:
            self.outline_data.coalesce(other.outline_data)
        if self.box_data is None:
            self.box_data = other.box_data
        else:
            self.box_data.coalesce(other.box_data)

    def correct_values(self):
        self.text_data.correct_values()
        if self.outline_data is not None:
            self.outline_data.coalesce(OutlineData.get_default())
            self.outline_data.correct_values()
        self.box_data.correct_values()

    pass

class Subtitle:

    def __init__(self, content:List[str]=None, style:Style=None):
        self.content = content
        self.style = style
        pass

    def __repr__(self) -> str:
        return str(self.__dict__)
    def __eq__(self, __value: object) -> bool:
        return self.__dict__ == __value.__dict__

class SubtitleGroup:

    def __init__(self, input_image_path:str=None, image_modified_time=None, output_image_path:str=None, subtitles:List[Subtitle]=None):
        
        self.input_image_path = input_image_path
        self.image_modified_time = image_modified_time
        self.output_image_path = output_image_path
        self.subtitles = subtitles
        
    def __repr__(self) -> str:
        return str(self.__dict__)
    def __eq__(self, __value: object) -> bool:
        return self.__dict__ == __value.__dict__