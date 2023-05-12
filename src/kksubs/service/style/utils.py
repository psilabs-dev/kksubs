from itertools import product
from typing import List

# general purpose tools for style.yaml file.

def _add_grid10_options(style_list:List):
    # adds grid10 combinations to the styles sheet.
    for i in range(10):
        for j in range(10):
            style_list.append({
                'style_id': f'grid{i}{j}',
                'box_data': {
                    'grid': f'[{i}, {j}]'
                }
            })
    return style_list

def _apply_grid10(style_list:List, style_id:str):
    # applies grid10 to the style ID
    for i in range(10):
        for j in range(10):
            style_list.append({
                'style_id': f'{style_id}{i}{j}({style_id}, grid{i}{j})'
            })
    return style_list

def apply_grid10(style_list, style_ids=None) -> list:
    if style_ids is None:
        style_ids = list(map(lambda kv:kv['style_id'], style_list))

    style_list = _add_grid10_options(style_list)
    if isinstance(style_ids, str):
        return _apply_grid10(style_list, style_ids)
    # assume style_ids is a list.
    for style_id in style_ids:
        style_list = _apply_grid10(style_list, style_id)
    return style_list

def _pwrap(text):
    if not text:
        return text
    return f"({text})"

def multiply_styles(style_list, *style_groups) -> list:
    # multiplies groups of styles together
    multiplied_style_ids = [''.join(items)+_pwrap(','.join(items)) for items in product(*style_groups)]
    for multiplied_style in multiplied_style_ids:
        style_list.append({'style_id': multiplied_style})

    return style_list
