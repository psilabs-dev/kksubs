from kksubs.data.abstract import *
from kksubs.utils.coalesce import *
from kksubs.utils.sanitizers import *

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