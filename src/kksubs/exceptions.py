
class InvalidProjectException(FileNotFoundError):
    "Project does not have a necessary directory to perform kksubs operations."
    def __init__(self, project_directory):
        self.project_directory = project_directory

class FolderCollisionException(Exception):
    def __init__(self):
        super().__init__("The library and workspace cannot be assigned the same directory.")