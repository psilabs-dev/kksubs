from typing import List
from PIL import Image, ImageDraw, ImageFont, ImageFilter
import textwrap

def _get_text_dimensions(text_string:str, font:ImageFont.FreeTypeFont, default_text_width=None, default_text_height=None):
    if text_string == "":
        return default_text_width, default_text_height
    _, descent = font.getmetrics()

    text_width = font.getmask(text_string).getbbox()[2]
    text_height = font.getmask(text_string).getbbox()[3] + descent

    return text_width, text_height

def create_text_layer(
        image:Image.Image, font:ImageFont.FreeTypeFont, content:List[str],
        color, size, stroke_color, stroke_size,
        align_h, align_v, box_width, coords
) -> Image.Image:
    image_width, image_height = image.size

    text_layer = Image.new("RGBA", image.size, (0, 0, 0, 0))
    text_draw = ImageDraw.Draw(text_layer)

    tb_anchor_x, tb_anchor_y = coords
    tb_anchor_x = image_width/2 + tb_anchor_x
    tb_anchor_y = image_height/2 - tb_anchor_y

    default_text_width, default_text_height = _get_text_dimensions("l", font)

    # analyze text
    wrapped_text = []
    for line in content:
        if line != "":
            wrapped_text.extend(textwrap.wrap(line, width=box_width))
        else:
            wrapped_text.append("")
    if not wrapped_text:
        return image

    text_dimensions = [_get_text_dimensions(line, font, default_text_width=default_text_width, default_text_height=default_text_height) for line in wrapped_text]
    text_widths = list(map(lambda dim:dim[0], text_dimensions))
    max_text_width = max(text_widths)
    num_lines = len(wrapped_text)
    sum_text_height = num_lines * default_text_height

    # gather rotation arguments. (for future advanced rotation)
    left = image_width
    right = 0
    up = image_height
    down = 0
    for line in wrapped_text:
        text_width = font.getlength(line)
        if align_h == "left":
            left = min(left, tb_anchor_x)
            right = max(right, tb_anchor_x + text_width)
        elif align_h == "center":
            left = min(left, tb_anchor_x - text_width/2)
            right = max(right, tb_anchor_x + text_width/2)
        elif align_h == "right":
            left = min(left, tb_anchor_x - text_width)
            right = max(right, tb_anchor_x)
    if align_v == "top":
        up = min(up, tb_anchor_y)
        down = max(down, tb_anchor_y + sum_text_height)
    elif align_v == "bottom":
        up = min(up, tb_anchor_y + sum_text_height)
        down = max(down, tb_anchor_y)
    elif align_v == "center":
        up = min(up, tb_anchor_y + sum_text_height)
        down = max(down, tb_anchor_y)
        pass

    # add text stage
    for i, line in enumerate(wrapped_text):
        text_width = font.getlength(line)

        if align_h == "left":
            x = tb_anchor_x + text_width/2 - text_width/2
        elif align_h == "center":
            x = tb_anchor_x - text_width/2
        elif align_h == "right":
            x = tb_anchor_x - text_width/2 - text_width/2
        else:
            raise ValueError(f"Invalid alignment value {align_h}.")
        if align_v == "up":
            y = tb_anchor_y - default_text_height*(num_lines-i)
        elif align_v == "down":
            y = tb_anchor_y - default_text_height*(num_lines-i) + sum_text_height
        elif align_v == "center":
            y = tb_anchor_y - default_text_height*(num_lines-i) + sum_text_height//2
        else:
            raise ValueError(f"Invalid push value {align_v}.")
        line_pos = (x, y)

        if stroke_size is not None:
            text_draw.text(line_pos, line, font=font, fill=color, stroke_width=stroke_size, stroke_fill=stroke_color)
            pass
        else:
            text_draw.text(line_pos, line, font=font, fill=color)

    return text_layer