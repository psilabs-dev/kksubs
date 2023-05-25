from typing import Optional
from PIL import ImageColor

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