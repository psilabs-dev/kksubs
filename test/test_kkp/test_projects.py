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
from pathlib import Path
import pytest

from common.exceptions import InvalidProjectException
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


@pytest.fixture
def test_environment():
    """Fixture providing test environment setup."""
    def setup_test(test_dir):
        workspace, game, library = create_test_site(test_dir)
        controller = ProjectController()
        controller.configure(metadata_directory=test_dir, game_directory=game, library=library, workspace=workspace)
        return controller, workspace, game, library
    return setup_test


def project_exists_in_library(library, project_name):
    return os.path.exists(os.path.join(library, project_name))


def test_project_operations(test_environment):
    with tempfile.TemporaryDirectory() as temp_dir:
        controller, workspace, game, library = test_environment(temp_dir)

        # create test project
        controller._create('test')
        assert project_exists_in_library(library, 'test')
        # cannot create a project within a project.
        with pytest.raises(FileExistsError):
            controller._create('test/2')


def test_merge_project(test_environment):
    with tempfile.TemporaryDirectory() as temp_dir:
        controller, workspace, game, library = test_environment(temp_dir)

        # create test project
        controller._create('test')
        controller._create('test2')

        character_file = os.path.join('UserData', 'chara', 'character.png')
        cap_file = os.path.join('UserData', 'cap', 'image.png')
        with open(os.path.join(library, 'test', character_file), 'w') as writer:
            writer.write("")
        with open(os.path.join(library, 'test', cap_file), 'w') as writer:
            writer.write("")

        assert not os.path.exists(os.path.join(game, character_file))
        assert not os.path.exists(os.path.join(game, cap_file))
        controller._merge_project('test')
        assert os.path.exists(os.path.join(game, character_file))
        assert not os.path.exists(os.path.join(game, cap_file))
