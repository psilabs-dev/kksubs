import unittest
from kksubs.data import BoxData, Style, TextData

from kksubs.service.extractors import extract_styles

class TestExtractStyles(unittest.TestCase):

    def test_basic(self):
        extract_styles_input = [
            {
                "style_id": "1",
                "text_data": {
                    "color": [255, 255, 255]
                },
                "box_data": {
                    "align_v": "left"
                }
            }
        ]
        styles = extract_styles(extract_styles_input)
        solution = Style(style_id="1", text_data=TextData(color=[255, 255, 255]), box_data=BoxData(align_v="left"))
        self.assertEqual(styles["1"], solution)

        pass

    def test_style_coalesce(self):

        text_style = TextData(font="default font")
        text_style.coalesce(TextData.get_default())
        solution = TextData.get_default()
        solution.font = "default font"
        self.assertEqual(text_style, solution)

    def test_style_coalesce_2(self):

        style_1 = Style(
            style_id="base-style",
            text_data=TextData(font="base font", size=20)
        )
        style_2 = Style(
            style_id="inherited-style",
            text_data=TextData(font="custom font")
        )
        style_2.coalesce(style_1)
        style_2.coalesce(Style.get_default())
        self.assertEqual(style_2.style_id, "inherited-style")
        self.assertEqual(style_2.text_data.font, "custom font")
        self.assertEqual(style_2.text_data.size, 20)

    def test_style_inheritance(self):
        styles_dict = [
            {
                "style_id": "base-style",
                "text_data": {
                    "font": "base font",
                    "size": 20,
                }
            },
            {
                "style_id": "inherited-style(base-style)",
                "text_data": {
                    "font": "custom font"
                }
            }
        ]
        styles = extract_styles(styles_dict)
        
        style_2 = styles["inherited-style"]
        self.assertEqual(style_2.style_id, "inherited-style")
        self.assertEqual(style_2.text_data.font, "custom font")
        self.assertEqual(style_2.text_data.size, 20)
        # print('pass')

    pass