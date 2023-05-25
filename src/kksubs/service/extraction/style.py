import logging
import re
from typing import List, Dict, Union

from kksubs.data.subtitle.style import *
from kksubs.data.subtitle.style_row_enum import STYLE_ROW_ENUM

logger = logging.getLogger(__name__)

def _get_inherited_style_ids(input_style_id) -> List[str]:
    # returns parent profile ID or None.
    match = re.search(r'\((.*?)\)', input_style_id)
    if match:
        return list(map(lambda grp: grp.strip(), match.group(1).split(",")))
    return []

def _process_single_style(style_data:Dict, styles:Dict[str, Style]):
    style = Style.from_dict(style_data)

    # style inheritance logic.
    parent_style_ids = _get_inherited_style_ids(style.style_id)
    for parent_style_id in parent_style_ids:
        if parent_style_id not in styles.keys():
            logger.error(f"Style ID {parent_style_id} not found.")
            continue
        parent_style = styles.get(parent_style_id)
        # style.coalesce(parent_style)
        style.inherit(parent_style)
    style.style_id = style.style_id.split("(")[0]

    if style.style_id in styles.keys():
        logger.warning(f"Style ID conflict: {style.style_id} already in styles; skipping.")
        return
    styles[style.style_id] = style
    return

def _process_matrix(style_data:Dict, styles:Dict[str, Style]):

    matrix = StyleMatrix()
    row_data_list:List[Union[str, List[Dict]]] = style_data.get('matrix')
    
    for row_data in row_data_list:
        row:StyleRow

        if isinstance(row_data, dict):
            row_id = row_data.get('row_id')
            style_data_list = row_data.get('styles')
            if row_id is not None:
                row = STYLE_ROW_ENUM.get(row_id)
                continue
            if style_data_list is not None and len(style_data_list) > 0:
                style_list = list(map(Style.from_dict, style_data_list))
                row = StyleRow(styles=style_list)
        else:
            raise TypeError(row_data, type(row_data))
        
        matrix.add_row(row)
        
    for style in matrix.out():
        styles[style.style_id] = style

    return

def _process_entity(style_data:Dict, styles:Dict[str, Style]):
    # check if entity is a style or style matrix.

    if 'style_id' in style_data:
        _process_single_style(style_data, styles)
    elif 'matrix' in style_data:
        _process_matrix(style_data, styles)
    
    return

def extract_styles(styles_contents:List[dict]) -> Dict[str, Style]:

    styles:Dict[str, Style] = dict()
    logger.debug(f"Extracting styles from {styles_contents}.")
    if not styles_contents:
        return styles
    
    for style_data in styles_contents:
        _process_entity(style_data, styles)
    
    return styles