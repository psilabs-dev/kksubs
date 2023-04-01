# Koikatsu Automated Subtitles

> Automate simple subtitle processing for Koikatsu stories.

## Topics:

1. Installation and Setup
1. Running a `kksubs` Project
1. Editing a Draft
    1. Edit Subtitle Content
    1. Customize Subtitle Style
1. The `styles.yml` file
    1. Style Inheritance
    1. Default Styles
1. Appendix
    1. Style Fields

## Installation and Setup
A Windows OS is required and Python 3.7+ is recommended.

Open a Python virtual environment and install the Git repository. For example:
```
>>> virtualenv venv
>>> .\venv\Scripts\activate
>>> pip install git+https://github.com/pain-text-format/kksubs.git
```

For an example project, see a "hello-world" project [here].

## Running a `kksubs` Project
A typical `kksubs` project structure looks like this:
```
- images/
    - 1.png
    - 2.png
    - ...
- drafts/
    - draft1.txt
    - draft2.txt
    - ...
- output/
    - draft1/
        - subtitled-1.png
        - subtitled-2.png
        - ...
    - draft2/
        - ...
    - ...
- styles.yml
```
Each text file in the `drafts/` directory is called a "draft". A draft contains subtitling information you want to apply to images in `images/`, and the subtitled image outputs go to the `output/` directory.

To apply subtitles from a draft (e.g. `draft1.txt`) to all the images (from the project directory, for example), run the following script:
```
from kksubs import add_subtitles
add_subtitles('.', 'draft1.txt')
```
You can also run this from the command line.
```
>>> kksubs-compose -d draft1.txt
```
See [commands](/src/kksubs/cmd/README.md) for more information.

## Editing a Draft
A basic `kksubs` draft has the following structure:

```
image_id: 1.png
content: Text for image 1.

image_id: 2.png
content: First line of text for image 2.
Second line of text for image 2.

image_id: 3.png
text_data.color: blue
content: Text for image 3.

...
```

There are three types of "environments" in a `kksubs` draft:

- **image environment**: start processing an image. Starts with an `image_id` header.
    - e.g. `image_id: 1.png`
- **content environment**: start applying a subtitle to an image. Starts with a `content` header. Multiple subtitles can be applied to the same image, separated by multiple content headers.
    - e.g. `content: Text for image 1.`
- **styling environment**: make local, stylistic adjustments to an image.
    - e.g. `text_data.color: blue`

### Edit Subtitle Content
Each subtitle contains exactly one content environment. The `content` "environment" is created with a content header, and contains the body of text you want to add to the image. For example,
```
content: This is some text
This is some more text

This is some final text
```
will strip the string after `content:` and apply it to the image as a multiline subtitle.

### Customize Subtitle Style
You can customize the style of a subtitle using style data. Two types of essential style data include:

- `text_data`: visual attributes of a subtitle
    - e.g. `size` (font size)
- `box_data`: position of a subtitle and its characters in relation to the image
    - e.g. `align_h` (horizontal alignment)

Style customization is achieved using style headers and "dotted" nested attributes. 

For example in the following, after adding "This is some normal text" to an image, we add "This is some text" to the same image with font size 12 and centered horizontal alignment/justification.
```
content: This is some normal text

text_data.size: 12
box_data.align_h: center
content: This is some text
```
For more information on what styles can be customized, see [style fields](#style-fields) or the code file at `src\kksubs\data.py`.

## The `styles.yml` file

To get a more automated process of styling subtitles, you use a `styles.yml` file. The `styles.yml` file stores a list of commonly used styles, which are applied to subtitles by referring to their ID as a header. For example, one can store a custom style as follows:
```
# styles.yml

- style_id: c12
  text_data:
    size: 12
  box_data:
    align_h: center
```
Then the previous draft is equivalent to
```
content: This is some normal text

c12: This is some text
```

### Style Inheritance
Properties of styles can be inherited using the syntax, and their properties can be overridden.
```
- style_id: parent
  text_data:
    size: 30
    color: white
- style_id: child(parent)
  text_data:
    size: 40
```
In this block, the `child` style assigns the same font color to a subtitle as its parent, but assigns a font size of 40 instead of 30.

Multiple and nested inheritance is allowed.
```
- style_id: parent1
- style_id: parent2
- style_id: child1(parent1, parent2)
- style_id: child2(child1)
```
In the case of multiple inheritance, inheritance is applied iteratively (e.g. `child1` inherits from `parent1` then inherits from `parent2`).

### Default Styles

The style ID "default" is given special status in `styles.yml`. If the `styles.yml` contains a style that has ID "default", it will apply this style (by default) to every subtitle of every image.

The style of a subtitle is determined at three levels, in decreasing overriding power but increasing scope:

- local styling environments in the draft
- references to the `styles.yml` file
- `default` style (if exists in `styles.yml`)
- factory default style (always exists)

The "factory" style is applied in the absence of any styling from the user side, in the draft or `styles.yml`.

---
# Appendix


## Style Fields

| style field ID | name | values | description |
| - | - | - | - |
| `text_data.font` | font | "default"<br/>path to a TTF font |
| `text_data.size` | font size | positive int | 
| `text_data.color` | font fill color | color<br/>[int, int, int] |
| `text_data.stroke_size` | font outline size | positive int<br/>0 |
| `text_data.stroke_color` | font outline color | color<br/>[int, int, int] |
| - | - | - |
| `box_data.align_h` | horizontal alignment | "left"<br/>"right"<br/>"center" |
| `box_data.align_v` | vertical alignment | "bottom"<br/>"top"<br/>"center" |
| `box_data.box_width` | text width | positive int |
| `box_data.anchor` | textbox anchor point | [int, int] | Anchors the subtitle textbox to a point on the image. Default position is the center of the image.<br/><br/>The anchor's positional relation to the textbox depends on horizontal and vertical alignment. |
