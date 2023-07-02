# TODO: test project database (CRUD) operations (on the controller level)

# test configuration
# test creating project (from blank project)
# test creating invalid project
# test creating project (from existing project)
# test is_project
# test listing project
# test checking out project (from blank project)
# test checkout invalid project
# test checkout project by number
# test checking out project (from existing project)
# test deleting project
# test delete project by number
# test delete invalid project
# test sync project (no project --> invalid)
# test sync project (has project)

import tempfile
import os
import unittest
from common.exceptions import InvalidProjectException
from pathlib import Path

from kkp.controller.project import ProjectController

def create_test_site(test_dir):
    workspace = os.path.join(test_dir, 'workspace')
    game = os.path.join(test_dir, 'Koikatsu Party')
    library = os.path.join(test_dir, 'library')
    user_data = os.path.join(game, 'UserData')
    cap = os.path.join(user_data, 'cap')
    chara = os.path.join(user_data, 'chara')

    os.makedirs(workspace, exist_ok=True)
    os.makedirs(game, exist_ok=True)
    os.makedirs(library, exist_ok=True)
    os.makedirs(user_data, exist_ok=True)
    os.makedirs(cap, exist_ok=True)
    os.makedirs(chara, exist_ok=True)
    return workspace, game, library

class TestProjectController(unittest.TestCase):

    def set_up_test(self, test_dir):
        self.workspace, self.game, self.library = create_test_site(test_dir)
        self.controller = ProjectController()
        self.controller.configure(metadata_directory=test_dir, game_directory=self.game, library=self.library, workspace=self.workspace)
    
    def project_exists_in_library(self, project_name):
        return os.path.exists(os.path.join(self.library, project_name))

    def test_project_operations(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            self.set_up_test(temp_dir)

            # create test project
            self.controller._create('test')
            self.assertTrue(self.project_exists_in_library('test'))
            # cannot create a project within a project.
            self.assertRaises(FileExistsError, self.controller._create, 'test/2')
            self.controller._create('test2')
            self.assertRaises(InvalidProjectException, self.controller.checkout, 'test3')
    
    def test_merge_project(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            self.set_up_test(temp_dir)

            # create test project
            self.controller._create('test')
            self.controller._create('test2')

            character_file = os.path.join('UserData', 'chara', 'character.png')
            cap_file = os.path.join('UserData', 'cap', 'image.png')
            with open(os.path.join(self.library, 'test', character_file), 'w') as writer:
                writer.write("")
            with open(os.path.join(self.library, 'test', cap_file), 'w') as writer:
                writer.write("")

            self.assertFalse(os.path.exists(os.path.join(self.game, character_file)))
            self.assertFalse(os.path.exists(os.path.join(self.game, cap_file)))
            self.controller._merge_project('test')
            self.assertTrue(os.path.exists(os.path.join(self.game, character_file)))
            self.assertFalse(os.path.exists(os.path.join(self.game, cap_file)))
