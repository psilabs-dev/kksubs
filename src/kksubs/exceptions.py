
class InvalidProjectException(FileNotFoundError):
    "Project does not have a necessary directory to perform kksubs operations."
    def __init__(self, project_directory):
        self.project_directory = project_directory
