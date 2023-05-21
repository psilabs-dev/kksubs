import os

class Project:
    def __init__(
            self, 
            project_directory:str=None,
            metadata_directory:str=None,
            state_directory:str=None,
            images_dir:str=None,
            drafts_dir:str=None,
            outputs_dir:str=None,
            styles_path:str=None,
    ):
        self.project_directory = project_directory
        self.metadata_directory = metadata_directory
        self.state_directory = state_directory
        self.images_dir = images_dir
        self.drafts_dir = drafts_dir
        self.outputs_dir = outputs_dir
        self.styles_path = styles_path

