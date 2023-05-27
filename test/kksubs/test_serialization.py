from typing import Type
import unittest

from common.data.representable import RepresentableData
from kksubs.data.subtitle.style_attributes import *
from kksubs.data.subtitle.style import *

class TestSerialization(unittest.TestCase):

    def assert_representations_equal(self, representable_data:RepresentableData, representation_class:Type[RepresentableData]):
        self.assertEqual(representable_data.serialize(), representation_class.deserialize(representable_data.serialize()).serialize())
        self.assertEqual(representation_class.deserialize(representable_data.serialize()), representable_data)

    def test_style_attribute_serialization(self):
        self.assert_representations_equal(TextData(), TextData)
        self.assert_representations_equal(TextData(font='abc'), TextData)
        self.assert_representations_equal(TextData(font='123', size=12, color=[1, 2, 3], stroke_color='white'), TextData)
        self.assert_representations_equal(OutlineData(), OutlineData)
        self.assert_representations_equal(BoxData(), BoxData)
        self.assert_representations_equal(Brightness(), Brightness)
        self.assert_representations_equal(Gaussian(), Gaussian)
        self.assert_representations_equal(Motion(), Motion)

    def test_style_serialization(self):
        self.assert_representations_equal(Style(), Style)