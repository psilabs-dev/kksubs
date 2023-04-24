import os
from typing import List
from PIL import Image, ImageFont, ImageFilter, ImageEnhance

from kksubs.data import OutlineData, Subtitle
from kksubs.service.processor.motion_blur import apply_motion_blur
from kksubs.service.processor.apply_text import create_text_layer

import logging

logger = logging.getLogger(__name__)

def get_pil_coordinates(image:Image.Image, anchor, grid4, nudge):
    image_width, image_height = image.size
    if grid4 is not None:
        grid4_x, grid4_y = grid4
        tb_anchor_x = int(image_width//4*grid4_x)
        tb_anchor_y = int(image_height//4*grid4_y)
    else:
        tb_anchor_x, tb_anchor_y = anchor
        tb_anchor_x = image_width/2 + tb_anchor_x
        tb_anchor_y = image_height/2 - tb_anchor_y
    if nudge is not None: # if there is anchor point data, use it to fine-tune.
        x_nudge, y_nudge = nudge
        tb_anchor_x = tb_anchor_x + x_nudge
        tb_anchor_y = tb_anchor_y - y_nudge

    return tb_anchor_x, tb_anchor_y

def add_subtitle_to_image(image:Image.Image, subtitle:Subtitle, project_directory:str) -> Image.Image:

    # expand subtitle.
    style = subtitle.style
    content = subtitle.content
    if not content:
        content = [""]
    # expand details of subtitle profile.
    text_data = style.text_data
    box_data = style.box_data

    # extract image data
    image_width, image_height = image.size

    # extract text data
    if text_data.font == "default":
        font_style = "arial.ttf"
    elif os.path.exists(text_data.font):
        font_style = text_data.font
    else:
        raise FileNotFoundError(text_data.font)
    
    # add default text data
    content[0] = text_data.text+content[0]
    
    font_color = text_data.color
    font_size = text_data.size
    font_stroke_size = text_data.stroke_size
    font_stroke_color = text_data.stroke_color
    align_h = box_data.align_h
    align_v = box_data.align_v
    box_width = box_data.box_width

    anchor = box_data.anchor
    grid4 = box_data.grid4
    nudge = box_data.nudge

    tb_anchor_x, tb_anchor_y = get_pil_coordinates(image, anchor=anchor, grid4=grid4, nudge=nudge)

    # apply sub styles
    styles = style.styles
    if styles is not None:
        for sub_style in styles:
            image = add_subtitle_to_image(image, Subtitle(content=[], style=sub_style), project_directory)

    font = ImageFont.truetype(font_style, font_size)
    
    text_layer = create_text_layer(image, font, content, font_color, font_size, font_stroke_color, font_stroke_size, align_h, align_v, box_width, tb_anchor_x, tb_anchor_y)
    
    # effect processing layer
    mask = style.mask
    has_mask = False
    if mask is not None:
        mask_path = mask.path
        if mask_path is not None:
            if not os.path.exists(mask_path):
                mask_path = os.path.join(project_directory, mask_path)
            if not os.path.exists(mask_path):
                raise FileNotFoundError(f"Mask file {mask_path} cannot be found.")
            mask_image = Image.open(mask_path)
            has_mask = True

    brightness = style.brightness
    if brightness is not None:
        brightness = brightness.value
        if brightness is not None:
            brightness_enhancer = ImageEnhance.Brightness(image)
            if has_mask:
                image.paste(brightness_enhancer.enhance(brightness), (0, 0), mask_image)
            else:
                image = brightness_enhancer.enhance(brightness)
    
    gaussian = style.gaussian
    if gaussian is not None:
        radius = gaussian.value
        if radius is not None:
            if has_mask:
                image.paste(image.filter(ImageFilter.GaussianBlur(radius=radius)), (0, 0), mask_image)
            else:
                image = image.filter(ImageFilter.GaussianBlur(radius=radius))

    motion = style.motion
    if motion is not None:
        kernel_size = motion.value
        angle = motion.angle
        if kernel_size is not None and angle is not None:
            if has_mask:
                image.paste(apply_motion_blur(image, kernel_size, angle), (0, 0), mask_image)
            else:
                image = apply_motion_blur(image, kernel_size, angle)

    background = style.background
    if background is not None:
        bg_path = background.path
        if bg_path is not None:
            if not os.path.exists(bg_path):
                bg_path = os.path.join(project_directory, bg_path)
            if not os.path.exists(bg_path):
                raise FileNotFoundError(f"Image file {bg_path} cannot be found.")
            bg_image = Image.open(bg_path)
            image.paste(bg_image, (0, 0), bg_image)

    # outline data application
    for outline_data in [style.outline_data_1, style.outline_data]:
        if outline_data is not None and isinstance(outline_data, OutlineData):
            outline_color = outline_data.color
            outline_size = outline_data.size
            outline_blur = outline_data.blur
            outline_alpha = outline_data.alpha
            outline_layer = create_text_layer(image, font, content, outline_color, font_size, outline_color, outline_size, align_h, align_v, box_width, tb_anchor_x, tb_anchor_y)
            outline_base = outline_layer
            if outline_blur is not None and isinstance(outline_blur, int) and outline_blur > 0:
                outline_base = image.copy()
                outline_base.paste(outline_layer, (0, 0), outline_layer)
                outline_base = outline_base.filter(ImageFilter.GaussianBlur(radius=outline_blur))
                outline_layer = outline_layer.filter(ImageFilter.GaussianBlur(radius=outline_blur)).convert("RGBA")
                if outline_alpha is not None and outline_alpha < 1:
                    outline_layer = ImageEnhance.Brightness(outline_layer.getchannel('A')).enhance(outline_alpha)
                pass
            # outline_layer.show()
            image.paste(outline_base, (0, 0), outline_layer)
            pass

    text_mask = text_layer
    if text_data.alpha is not None and text_data.alpha < 1:
        text_mask = ImageEnhance.Brightness(text_mask.getchannel('A')).enhance(text_data.alpha)

    image.paste(text_layer, (0, 0), text_mask)
    
    return image

def add_subtitles_to_image(image:Image.Image, subtitles:List[Subtitle], project_directory:str) -> Image.Image:
    for subtitle in subtitles:
        image = add_subtitle_to_image(image, subtitle, project_directory)
    return image
