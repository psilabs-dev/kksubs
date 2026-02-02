import logging
import os
from typing import Dict, List

from kksubs.data.abstract import RepresentableData
from kksubs.data.subtitle.style import Style

logger = logging.getLogger(__name__)

class Subtitle(RepresentableData):

    def __init__(self, content:List[str]=None, style:Style=None):
        if style is None:
            style = Style()

        self.content = content
        self.style = style
        pass

    @classmethod
    def deserialize(self, subtitle_data:Dict) -> "Subtitle":
        if subtitle_data is None:
            return None

        return Subtitle(content=subtitle_data.get('content'), style=Style.deserialize(subtitle_data.get('style')))

class CharacterDialogueSubtitle(Subtitle):

    def __init__(self, dialogue_content:List[str]=None, style:Style=None):
        super().__init__(content=[], style=style)
        if dialogue_content is None:
            dialogue_content = []
        self.dialogue_content = dialogue_content

    @classmethod
    def deserialize(self, subtitle_data:Dict) -> "CharacterDialogueSubtitle":
        if subtitle_data is None:
            return None

        return CharacterDialogueSubtitle(
            dialogue_content=subtitle_data.get('dialogue_content'),
            style=Style.deserialize(subtitle_data.get('style'))
        )

class SubtitleGroup(RepresentableData):

    def __init__(self, image_id:str=None, input_image_path:str=None, image_modified_time=None, output_image_path:str=None, subtitles:List[Subtitle]=None):

        self.image_id = image_id
        self.input_image_path = input_image_path
        self.image_modified_time = image_modified_time
        self.output_image_path = output_image_path
        self.subtitles = subtitles

    @classmethod
    def deserialize(self, data:Dict) -> "SubtitleGroup":
        if data is None:
            return SubtitleGroup()
        subtitle_datas = data.get('subtitles')
        subtitles = list(map(Subtitle.deserialize, subtitle_datas)) if subtitle_datas is not None else None
        return SubtitleGroup(
            image_id=data.get('image_id'),
            input_image_path=data.get('input_image_path'),
            image_modified_time=data.get('image_modified_time'),
            output_image_path=data.get('output_image_path'),
            subtitles=subtitles
        )

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
