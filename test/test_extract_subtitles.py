from typing import Dict, List
import unittest
from kksubs.data import BoxData, Style, Subtitle, TextData

from kksubs.service.extractors import extract_subtitles, is_valid_nested_attribute

class TestExtractSubtitles(unittest.TestCase):

    def assert_contents_equal(self, subtitles:Dict[str, List[Subtitle]], solution:Dict[str, List[Subtitle]]):
        for key in solution:
            self.assertListEqual(list(map(lambda subtitle: subtitle.content, subtitles[key])), list(map(lambda subtitle: subtitle.content, solution[key])))

    def test_basic(self):
        
        read_input = "image_id: 1.png\ncontent: some content\ncontent: some more content"
        subtitles = extract_subtitles(draft_body=read_input, styles=dict())
        solution = {
            "1.png": [
                Subtitle(content=["some content"], style=Style.get_default().corrected()),
                Subtitle(content=["some more content"], style=Style.get_default().corrected()),
            ]
        }

        self.assertEqual(subtitles.keys(), solution.keys())
        self.assert_contents_equal(subtitles, solution)
        self.assertDictEqual(subtitles, solution)
        pass

    def test_two_images(self):

        # self.maxDiff = None

        read_input = "image_id: 1.png\ncontent: some content\nimage_id: 2.png"
        subtitles = extract_subtitles(draft_body=read_input, styles=dict())
        solution = {
            "1.png": [
                Subtitle(content=["some content"], style=Style.get_default().corrected()),
                # Subtitle(content=["some more content"], style=Style.get_default()),
            ],
            "2.png": [
                Subtitle(content=[], style=Style.get_default().corrected())
            ]
        }

        self.assertEqual(subtitles.keys(), solution.keys())
        self.assert_contents_equal(subtitles, solution)
        self.assertDictEqual(subtitles, solution)
        pass

    def test_multiline(self):
        read_input = "image_id: 1.png\ncontent: first line\nsecond line"
        subtitles = extract_subtitles(draft_body=read_input, styles=dict())
        solution = {
            "1.png": [
                Subtitle(content=["first line", "second line"], style=Style.get_default().corrected()),
            ]
        }

        self.assertEqual(subtitles.keys(), solution.keys())
        self.assert_contents_equal(subtitles, solution)
        self.assertDictEqual(subtitles, solution)
        pass

    def test_is_valid_nested_attributes(self):
        self.assertTrue(is_valid_nested_attribute(Style(), nested_attribute="style_id"))
        self.assertTrue(is_valid_nested_attribute(Style(), nested_attribute="text_data.font"))
        self.assertTrue(is_valid_nested_attribute(Style(), nested_attribute="text_data.size"))

    def test_extract_styled_subtitles(self):
        read_input = """
image_id: 1.png
text_data.font: default font
text_data.size: 123
text_data.color: [1, 2, 3]

content: some content

"""
        subtitles = extract_subtitles(draft_body=read_input, styles=dict())

        solution = {
            "1.png": [
                Subtitle(
                    content=["some content"], 
                    style=Style(
                        text_data=TextData(
                            font="default font",
                            size=123,
                            color=(1, 2, 3),
                        ),
                        box_data=BoxData.get_default()
                    )
                ),
            ],
        }
        solution['1.png'][0].style.coalesce(Style.get_default())

        # print(subtitles)
        # print(subtitles['1.png'][0])
        # print(solution['1.png'][0])

        self.assertEqual(subtitles.keys(), solution.keys())
        self.assert_contents_equal(subtitles, solution)
        self.assertDictEqual(subtitles, solution)
        pass

    pass