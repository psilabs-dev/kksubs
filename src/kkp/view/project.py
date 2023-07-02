

from typing import List


class ProjectView:

    def select_projects_from_list(self, current_project, project_list) -> List[str]:
        print('Please select a project from the following:')
        print(f'current project - {current_project}')
        for i, project in enumerate(project_list):
            print(f'            [{i}] - {project}')
        selection = input('Select numbers (separate by space) or enter \"A\" to select all: ')
        if selection == 'A':
            project_names = project_list
        else:
            selections = selection.split()
            project_names = list(map(lambda s:project_list[int(s)], selections))
        return project_names

    def select_project_from_list(self, current_project, project_list):
        print('Please select a project from the following:')
        print(f'current project - {current_project}')
        for i, project in enumerate(project_list):
            print(f'            [{i}] - {project}')
        selection = input('Select a number: ')
        selection = int(selection)
        project_name = project_list[selection]
        return project_name
    
    def confirm_project_checkout(self, source, destination) -> bool:
        print('Confirm checkout:')
        print(f' - source:      {source}')
        print(f' - destination: {destination}')
        confirm = input('Enter Y to confirm: ') == 'Y'
        return confirm