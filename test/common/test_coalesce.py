import unittest
from common.utils.coalesce import coalesce

class TestCoalesce(unittest.TestCase):

    def test_coalesce(self):

        self.assertEqual(coalesce(None, None, None), None)
        self.assertEqual(coalesce(1, 2, 3), 1)
        self.assertEqual(coalesce(1, None, None), 1)
        self.assertEqual(coalesce(None, 1, None), 1)
        self.assertEqual(coalesce(), None)
