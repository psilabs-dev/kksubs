import logging
import os
from typing import List

from kksubs.utils.sanitizers import *
from kksubs.data.abstract import *
from kksubs.data.subtitle.style_attributes import *
from kksubs.data.subtitle.style import Style

logger = logging.getLogger(__name__)

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
