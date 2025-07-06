from typing import Type

from common.data.representable import RepresentableData
from kksubs.data.subtitle.style_attributes import *
from kksubs.data.subtitle.style import *
from kksubs.data.subtitle.subtitle import *


def assert_representations_equal(representable_data: RepresentableData, representation_class: Type[RepresentableData]):
    assert representable_data.serialize() == representation_class.deserialize(representable_data.serialize()).serialize()
    assert representation_class.deserialize(representable_data.serialize()) == representable_data


def test_style_attribute_serialization():
    assert_representations_equal(TextData(), TextData)
    assert_representations_equal(TextData(font='abc'), TextData)
    assert_representations_equal(TextData(font='123', size=12, color=[1, 2, 3], stroke_color='white'), TextData)
    assert_representations_equal(OutlineData(), OutlineData)
    assert_representations_equal(BoxData(), BoxData)
    assert_representations_equal(Brightness(), Brightness)
    assert_representations_equal(Gaussian(), Gaussian)
    assert_representations_equal(Motion(), Motion)
    assert_representations_equal(Asset(), Asset)


def test_style_serialization():
    assert_representations_equal(Style(), Style)


def test_subtitle_serialization():
    assert_representations_equal(Subtitle(), Subtitle)
    assert_representations_equal(Subtitle(style=Style(background=Background(path='abcd'))), Subtitle)


def test_subtitle_group_serialization():
    assert_representations_equal(SubtitleGroup(), SubtitleGroup)