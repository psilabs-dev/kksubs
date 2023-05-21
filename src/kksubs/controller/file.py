# movement of files.

class FileController:

    def __init__(
            self,
            game_directory:str,
            library:str,
            workspace:str,
    ):
        self.game_directory = game_directory
        self.library = library
        self.workspace = workspace

    def checkout(self, project_name):
        ...

    def create(self, project_name):
        ...

    def list_projects(self, pattern:str):
        ...

    def delete(self, project_name:str):
        ...

    def sync(self):
        ...