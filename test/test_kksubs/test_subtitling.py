# unfortunately it's not easy to verify whether the subtitling program produces the intended image,
# and adding images as tests will take up quite a bit of unnecessary space
# so we will only check whether the subtitling program successfully produces an image to begin with.
# will test these at the controller level.

# TODO: mainly test the compose function.

# given a couple of (generated) images, and many various combinations of subtitle configurations, apply subtitles.
# given a couple images, and a script/draft, apply subtitles.
# given a couple images, several drafts, a styles.yml file, apply subtitles.
# given a couple images, a script, apply subtitles once with incremental update. Update draft then apply again.
# same thing but with images.
# same thing but with styles.
# same thing but run compose without incremental updating. Then run again with incremental updating.

from PIL import Image
import tempfile
import os
import pytest

from kksubs.controller.subtitle import SubtitleController


def generate_images(directory, images):
    for image_path in images:
        image = Image.new('RGB', (800, 600), (255, 255, 255))
        image.save(os.path.join(directory, image_path))
        image.close()


@pytest.fixture
def test_images():
    """Fixture providing test image list."""
    return list(map(lambda i: f'{i}.png', range(5)))


@pytest.fixture
def controller_setup():
    """Fixture providing controller setup function."""
    def setup_workspace(test_dir):
        return SubtitleController(test_dir)
    return setup_workspace


def test_create_project(controller_setup):
    with tempfile.TemporaryDirectory() as test_dir:
        controller = controller_setup(test_dir)
        controller.create()


def test_add_subtitles(controller_setup, test_images):
    with tempfile.TemporaryDirectory() as test_dir:
        controller = controller_setup(test_dir)
        controller.create()
        assert os.path.exists(test_dir)
        generate_images(controller.get_image_directory(), test_images)
        assert sorted(os.listdir(controller.get_image_directory())) == sorted(test_images)
        assert len(os.listdir(controller.get_scripts_directory())) == 1
        controller.add_subtitles(allow_multiprocessing=False)
        script = controller.get_scripts()[0]
        assert sorted(os.listdir(controller.get_output_directory_by_script(script))) == sorted(test_images)