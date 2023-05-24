from abc import ABC, abstractclassmethod, abstractmethod
import logging
import os
from PIL import ImageColor
from typing import List, Optional

from kksubs.utils.coalesce import coalesce

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

def to_string(value) -> Optional[str]:
    if value is None or isinstance(value, str):
        return value
    raise TypeError(type(value))

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

class TextData(BaseData):
    field_name = "text_data"

    def __init__(
            self, 
            font=None, 
            size=None, color=None, 
            stroke_size=None, stroke_color=None,
            text=None,
            alpha=None,
    ):
        self.font = font
        self.size = size
        self.color = color
        self.stroke_size = stroke_size
        self.stroke_color = stroke_color
        self.text = text
        self.alpha = alpha
        pass

    @classmethod
    def get_default(cls):
        return TextData(
            font="default", 
            size=60, color="white",
            stroke_size=0, stroke_color=(0, 0, 0),
            text="",
            alpha=1,
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
        self.alpha = coalesce(self.alpha, other.alpha)
        self.text = coalesce(self.text, other.text)

    def correct_values(self):
        if self.font is not None:
            assert(isinstance(self.font, str))

        self.size = to_integer(self.size)
        self.color = to_rgb_color(self.color)
        self.stroke_size = to_integer(self.stroke_size)
        self.stroke_color = to_rgb_color(self.stroke_color)
        self.alpha = to_float(self.alpha)
        self.text = to_string(self.text)

    pass

class OutlineData(BaseData):
    field_name = "outline_data"

    def __init__(
            self,
            color=None, size=None, blur=None, alpha=None,
    ):
        self.color = color
        self.size = size
        self.blur = blur
        self.alpha = alpha
        pass

    @classmethod
    def get_default(cls):
        return OutlineData(
            color="yellow",
            size=5,
            blur=0,
            alpha=1,
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
        self.alpha = coalesce(self.alpha, other.alpha)

    def correct_values(self):
        self.color = to_rgb_color(self.color)
        self.size = to_integer(self.size)
        self.blur = to_integer(self.blur)
        self.alpha = to_float(self.alpha)

class OutlineData1(OutlineData):
    field_name = "outline_data_1"

class BoxData(BaseData):
    field_name = "box_data"

    def __init__(
            self, 
            align_h=None, align_v=None, 
            box_width=None, 
            anchor=None,
            grid4=None,
            grid10=None,
            nudge=None,
            rotate=None,
    ):
        self.align_h = align_h
        self.align_v = align_v
        self.box_width = box_width
        self.anchor = anchor
        self.grid4 = grid4
        self.grid10 = grid10
        self.nudge = nudge
        self.rotate = rotate
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

        if self.anchor is None and self.grid4 is None and self.grid10 is None:
            self.anchor = other.anchor
            self.grid4 = other.grid4
            self.grid10 = other.grid10

        self.nudge = coalesce(self.nudge, other.nudge)
        self.rotate = coalesce(self.rotate, other.rotate)

    def correct_values(self):
        self.align_h = to_validated_value(self.align_h, {"left", "right", "center"})
        self.align_v = to_validated_value(self.align_v, {"bottom", "top", "center"})
        self.box_width = to_integer(self.box_width)
        self.anchor = to_xy_coords(self.anchor)
        self.grid4 = to_xy_coords(self.grid4)
        self.grid10 = to_xy_coords(self.grid10)
        self.nudge = to_xy_coords(self.nudge)
        self.rotate = to_integer(self.rotate)

class Brightness(BaseData):
    field_name = "brightness"

    def __init__(
            self,
            value=None,
    ):
        self.value = value
        pass

    @classmethod
    def get_default(cls):
        return Brightness(
            value=1.0
        )
    
    @classmethod
    def from_dict(cls, values=None):
        if values is None:
            return None
        return Brightness(**values)
    
    def coalesce(self, other:"Brightness"):
        if other is None:
            return
        self.value = coalesce(self.value, other.value)

    def correct_values(self):
        self.value = to_float(self.value)

    pass

class Gaussian(BaseData):
    field_name = "gaussian"

    def __init__(
            self,
            value=None, # radius
    ):
        self.value = value
        pass

    @classmethod
    def get_default(cls):
        return Gaussian(
            value=0
        )
    
    @classmethod
    def from_dict(cls, values=None):
        if values is None:
            return None
        return Gaussian(**values)
    
    def coalesce(self, other:"Gaussian"):
        if other is None:
            return
        self.value = coalesce(self.value, other.value)

    def correct_values(self):
        self.value = to_integer(self.value)

    pass

class Motion(BaseData):
    field_name = "motion"

    def __init__(
            self,
            value=None, # kernel size
            angle=None, # value between 0 and 360
    ):
        self.value = value
        self.angle = angle
        pass

    @classmethod
    def get_default(cls):
        return Motion(
            value=0,
            angle=0,
        )
    
    @classmethod
    def from_dict(cls, values=None):
        if values is None:
            return None
        return Motion(**values)
    
    def coalesce(self, other:"Motion"):
        if other is None:
            return
        self.value = coalesce(self.value, other.value)
        self.angle = coalesce(self.angle, other.angle)

    def correct_values(self):
        self.value = to_integer(self.value)
        self.angle = to_integer(self.angle)

    pass

class Mask(BaseData):
    field_name = "mask"

    def __init__(
            self,
            path=None,
    ):
        self.path = path
        pass

    @classmethod
    def get_default(cls):
        return Mask(
        )
    
    @classmethod
    def from_dict(cls, path=None):
        if path is None:
            return None
        return Mask(**path)
    
    def coalesce(self, other:"Mask"):
        if other is None:
            return
        self.path = coalesce(self.path, other.path)

    def correct_values(self):
        return

    pass

class Background(BaseData):
    field_name = "background"

    def __init__(
            self,
            path=None,
    ):
        self.path = path
        pass

    @classmethod
    def get_default(cls):
        return Background(
        )
    
    @classmethod
    def from_dict(cls, path=None):
        if path is None:
            return None
        return Background(**path)
    
    def coalesce(self, other:"Background"):
        if other is None:
            return
        self.path = coalesce(self.path, other.path)

    def correct_values(self):
        return

    pass

class Style(BaseData):
    field_name = "style"

    def __init__(
            self, 
            style_id:str=None, 
            text_data:TextData=None,
            outline_data:OutlineData=None,
            outline_data_1:OutlineData1=None,
            box_data:BoxData=None,
            brightness:Brightness=None,
            gaussian:Gaussian=None,
            motion:Motion=None,
            background:Background=None,
            mask:Mask=None,
            styles:List["Style"]=None,
    ):
        self.style_id = style_id
        self.text_data = text_data
        self.outline_data = outline_data
        self.outline_data_1 = outline_data_1
        self.box_data = box_data
        self.brightness = brightness
        self.gaussian = gaussian
        self.motion = motion
        self.background = background
        self.mask = mask
        self.styles = styles
        pass

    @classmethod
    def get_default(cls):
        return Style(
            style_id="",
            text_data=TextData.get_default(),
            # stroke_data=StrokeData.get_default(),
            box_data=BoxData.get_default(),
            # styles=[]
        )

    @classmethod
    def from_dict(cls, style_dict:dict=None):
        if style_dict is None:
            return Style()
        return Style(
            style_id=style_dict.get("style_id"),
            text_data=TextData.from_dict(text_style_dict=style_dict.get(TextData.field_name)),
            outline_data=OutlineData.from_dict(outline_dict=style_dict.get(OutlineData.field_name)),
            outline_data_1=OutlineData1.from_dict(outline_dict=style_dict.get(OutlineData1.field_name)),
            box_data=BoxData.from_dict(box_style_dict=style_dict.get(BoxData.field_name)),
            brightness=Brightness.from_dict(values=style_dict.get(Brightness.field_name)),
            gaussian=Gaussian.from_dict(values=style_dict.get(Gaussian.field_name)),
            motion=Motion.from_dict(values=style_dict.get(Motion.field_name)),
            background=Background.from_dict(path=style_dict.get(Background.field_name)),
            mask=Background.from_dict(path=style_dict.get(Mask.field_name)),
            styles=[Style.from_dict(style_dict=sub_style_dict) for sub_style_dict in style_dict.get("styles")] if "styles" in style_dict.keys() else None,
        )
    
    def coalesce(self, other:"Style", essential=False):
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
        if self.outline_data_1 is None:
            self.outline_data_1 = other.outline_data_1
        else:
            self.outline_data_1.coalesce(other.outline_data_1)
        if self.box_data is None:
            self.box_data = other.box_data
        else:
            self.box_data.coalesce(other.box_data)
        if essential:
            return
        
        if self.brightness is None:
            self.brightness = other.brightness
        else:
            self.brightness.coalesce(other.brightness)
        if self.gaussian is None:
            self.gaussian = other.gaussian
        else:
            self.gaussian.coalesce(other.gaussian)
        if self.motion is None:
            self.motion = other.motion
        else:
            self.motion.coalesce(other.motion)
        if self.background is None:
            self.background = other.background
        else:
            self.background.coalesce(other.background)
        if self.mask is None:
            self.mask = other.mask
        else:
            self.mask.coalesce(other.mask)
        if not self.styles:
            self.styles = other.styles

    def correct_values(self):
        self.text_data.correct_values()
        if self.outline_data is not None:
            self.outline_data.coalesce(OutlineData.get_default())
            self.outline_data.correct_values()
        if self.outline_data_1 is not None:
            self.outline_data_1.coalesce(OutlineData1.get_default())
            self.outline_data_1.correct_values()
        self.box_data.correct_values()
        if self.brightness is not None:
            self.brightness.coalesce(Brightness.get_default())
            self.brightness.correct_values()
        if self.gaussian is not None:
            self.gaussian.coalesce(Gaussian.get_default())
            self.gaussian.correct_values()
        if self.motion is not None:
            self.motion.coalesce(Motion.get_default())
            self.motion.correct_values()
        if self.background is not None:
            self.background.coalesce(Background.get_default())
            self.background.correct_values()
        if self.mask is not None:
            self.mask.coalesce(Mask.get_default())
            self.mask.correct_values()
        if self.styles is not None:
            for style in self.styles:
                style.correct_values()
                style.coalesce(self, essential=True)

    pass

class Subtitle(RepresentableData):

    def __init__(self, content:List[str]=None, style:Style=None):
        self.content = content
        self.style = style
        pass

class SubtitleGroup(RepresentableData):

    def __init__(self, image_id:str=None, input_image_path:str=None, image_modified_time=None, output_image_path:str=None, subtitles:List[Subtitle]=None):
        
        self.image_id = image_id
        self.input_image_path = input_image_path
        self.image_modified_time = image_modified_time
        self.output_image_path = output_image_path
        self.subtitles = subtitles

    def complete_path_info(self, draft_id:str, image_id:str, image_dir:str, output_dir:str, prefix:str=None, suffix:str=None):
        if prefix is None:
            prefix = ""
        if suffix is None:
            suffix = ""

        image_name, extension = os.path.splitext(image_id)
        self.image_id = prefix + image_name + suffix + extension
        self.input_image_path = os.path.join(image_dir, image_id)
        self.image_modified_time = os.path.getmtime(self.input_image_path)
        self.output_image_path = os.path.join(output_dir, draft_id, prefix + image_name + suffix + extension)
