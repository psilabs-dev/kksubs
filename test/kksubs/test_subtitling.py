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
import unittest
import os

from kksubs.controller.subtitle import SubtitleController

def generate_images(directory, images):
    for image_path in images:
        image = Image.new('RGB', (800, 600), (255, 255, 255))
        image.save(os.path.join(directory, image_path))
        image.close()
    return

class TestSubtitling(unittest.TestCase):

    def setUp(self) -> None:
        self.test_dir = None
        self.controller = None
        self.images = list(map(lambda i:f'{i}.png', range(5)))

    def set_up_workspace(self, test_dir):
        self.test_dir = test_dir
        self.controller = SubtitleController(test_dir)

    def test_create_project(self):
        with tempfile.TemporaryDirectory() as test_dir:
            self.set_up_workspace(test_dir)
            self.controller.create()

    def test_add_subtitles(self):
        with tempfile.TemporaryDirectory() as test_dir:
            self.set_up_workspace(test_dir)
            self.controller.create()
            self.assertTrue(os.path.exists(test_dir))
            generate_images(self.controller.get_image_directory(), self.images)
            self.assertListEqual(os.listdir(self.controller.get_image_directory()), self.images)
            self.assertTrue(len(os.listdir(self.controller.get_scripts_directory())), 1)
            self.controller.add_subtitles(allow_multiprocessing=False)
            script = self.controller.get_scripts()[0]
            self.assertListEqual(os.listdir(self.controller.get_output_directory_by_script(script)), self.images)