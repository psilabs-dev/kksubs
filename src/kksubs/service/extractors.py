import logging
import re
from typing import Dict, List, Set

from kksubs.data import Background, BaseData, BoxData, Brightness, Gaussian, OutlineData, Style, Subtitle, TextData

# parsing/extraction, filtering, standardization
logger = logging.getLogger(__name__)

default_style_by_field_name:Dict[str, BaseData] = {
    base_data.field_name:base_data for base_data in [
        TextData, OutlineData, BoxData, 
        Brightness, Gaussian, Background, 
        Style
    ]
}

def get_inherited_style_ids(input_style_id) -> List[str]:
    # returns parent profile ID or None.
    match = re.search(r'\((.*?)\)', input_style_id)
    if match:
        return list(map(lambda grp: grp.strip(), match.group(1).split(",")))
    return []

def is_valid_nested_attribute(style:BaseData, nested_attribute:str) -> bool:
    attributes = nested_attribute.split(".")
    if len(attributes) == 1:
        return hasattr(style, attributes[0])
    
    # check if attribute corresponds to a style.
    if attributes[0] in default_style_by_field_name.keys():
        return is_valid_nested_attribute(default_style_by_field_name[attributes[0]](), ".".join(attributes[1:]))
    
    raise KeyError(style.field_name, nested_attribute)

def give_attributes_to_style(base_style:Style, attributes:List[str], value):
    # print(attributes, type(base_style))
    
    if len(attributes) == 1:
        return setattr(base_style, attributes[0], value)
    
    if getattr(base_style, attributes[0]) is None:
        setattr(base_style, attributes[0], default_style_by_field_name[attributes[0]]())
    return give_attributes_to_style(getattr(base_style, attributes[0]), attributes[1:], value)

def add_data_to_style(line:str, subtitle:Subtitle, styles:Dict[str, Style]):
    # adds data to style.

    key, value = line.split(":", 1)
    value = value.strip()
    
    if key == "style_id":
        # replace style with style ID.
        subtitle.style = styles.get(value)
    
    else:
        attributes = key.split(".")
        give_attributes_to_style(subtitle.style, attributes, value)

    pass

def extract_subtitles_from_image_block(textstring:str, content_keys:Set[str], styles:Dict[str, Style]) -> List[Subtitle]:
    
    subtitles:List[Subtitle] = []
    lines = textstring.strip().split("\n")
    in_content_environment = False
    in_style_environment = False
    is_start_of_subtitle = True

    def get_has_content_key(line:str):
        return any(line.startswith(key+":") for key in content_keys)
    
    def get_has_attr_key(line:str):
        # print(line, line.split(":", 1))
        if len(line.split(":", 1)) == 2:
            # print("ping")
            return is_valid_nested_attribute(default_style_by_field_name["style"](), line.split(":")[0])
        return False
        # return any(line.startswith(key+":") for key in style_keys)
    
    empty_lines:List[str]
    content:List[str]
    for i, line in enumerate(lines):
        # identify the start of a subtitle.

        has_content_key = get_has_content_key(line)
        has_style_key = get_has_attr_key(line)
        # has_next_line = i+1 <= len(lines)-1

        # state check.
        if not in_style_environment and has_style_key:
            is_start_of_subtitle = True
            in_content_environment = False
            in_style_environment = True
        elif not in_content_environment and has_content_key:
            is_start_of_subtitle = not in_style_environment or i==0
            in_style_environment = False
            in_content_environment = True
        elif in_content_environment and has_content_key:
            is_start_of_subtitle = True
        else:
            is_start_of_subtitle = False

        if is_start_of_subtitle:
            style = Style()
            content = []
            empty_lines = []
            subtitle = Subtitle(content=content, style=style)
            subtitles.append(subtitle)

        # content environment logic
        if in_content_environment:
            if has_content_key:
                lsplit = line.split(":", 1)
                if len(lsplit) == 2:
                    key, line_content = lsplit
                    if key == "content":
                        pass
                    else: # apply alias as style.
                        style.coalesce(styles.get(key))
                else:
                    line_content = ""

                line_content = lsplit[1].lstrip() if len(lsplit) == 2 else ""
            else:
                line_content = line
            if not line_content:
                empty_lines.append(line_content)
            else:
                content += empty_lines
                empty_lines = []
                content.append(line_content)

        # style logic
        if in_style_environment:
            if has_style_key:
                add_data_to_style(line, subtitle, styles)
            pass

        # print(
        #     int(is_start_of_subtitle), 
        #     int(in_content_environment),
        #     int(in_attr_environment),
        #     "line: ", line
        # )

    # correct subtitle styling data.
    for subtitle in subtitles:
        subtitle.style.coalesce(styles.get("default"))
        subtitle.style.coalesce(Style.get_default())
        subtitle.style.correct_values()

    # print(lines)
    # print(subtitles)
    return subtitles

def extract_styles(styles_contents:List[dict]) -> Dict[str, Style]:

    styles = dict()
    logger.debug(f"Extracting styles from {styles_contents}.")
    if not styles_contents:
        return styles
    
    for style_dict in styles_contents:
        style = Style.from_dict(style_dict=style_dict)

        # style inheritance logic.
        parent_style_ids = get_inherited_style_ids(style.style_id)
        for parent_style_id in parent_style_ids:
            if parent_style_id not in styles.keys():
                logger.error(f"Style ID {parent_style_id} not found.")
                continue
            parent_style = styles.get(parent_style_id)
            style.coalesce(parent_style)
        style.style_id = style.style_id.split("(")[0]

        if style.style_id in styles.keys():
            logger.warning(f"Style ID conflict: {style.style_id} already in styles; skipping.")
            continue
        styles[style.style_id] = style
        pass
    
    return styles

def extract_subtitles(draft_body:str, styles:Dict[str, Style]) -> Dict[str, List[Subtitle]]:
    # extract subtitles from draft
    logger.info(f"Extracting subtitles.")

    subtitles = dict()
    content_keys = {"content"}.union(styles.keys())

    # remove comments
    draft_body = "\n".join(list(filter(lambda line:not line.startswith("#"), draft_body.split("\n"))))

    # split lines for draft
    image_blocks = draft_body.split("image_id:")

    for image_block in image_blocks:
        image_block = image_block.strip()

        if not image_block:
            continue

        # add subtitles.
        image_block_split = image_block.split("\n", 1)
        image_id = image_block_split[0].strip()

        if len(image_block_split) == 1:
            subtitles[image_id] = [Subtitle([], style=Style.get_default().corrected())]
            continue

        image_subtitles = extract_subtitles_from_image_block(image_block_split[1], content_keys, styles)
        
        # print(image_subtitles)
        subtitles[image_id] = image_subtitles
    
    return subtitles
