# Drafts

Drafts are the main way of adding subtitles to an image. A basic draft that adds the text "Hello World" to the image `1.png` is:
```
image_id: 1.png
content: Hello World
```
> Note: the keys `image_id` and `content` are required components of the draft syntax.

The line `content: Hello World` represents a "subtitle", and the subtitle is being applied to `1.png`.

Multiline text is supported.
```
image_id: 1.png
content: first line of text
second line of text
```

Multiple subtitles can be added to multiple respective images in the same draft.
```
image_id: 1.png
content: (subtitle text for image 1)

image_id: 2.png
content: (subtitle text for image 2)

...
```
A subtitle can be customized with a style field. For example, the following subtitle adds red text to an image.
```
image_id: 1.png
text_data.color: red
content: (some red text)
```
The same subtitle can be customized with multiple styles.
```
image_id: 1.png
text_data.color: blue
text_data.size: 10
content: (some content)
```
> A list of valid style fields are found [here](styles.md).

The same image may be subtitled multiple times. For example, the following draft adds one subtitle to the left and right parts of `1.png`.
```
image_id: 1.png
box_data.anchor_point: [-100, 0]
content: (first subtitle text)

box_data.anchor_point: [100, 0]
content: (second subtitle text)
```
Comments can be added to a draft using `#`, which are ignored by the parser.
```
image_id: 1.png
# comment
content: (some content)
```

## Styles.yml
As mentioned, we can style a subtitle in the draft file,
```
image_id: 1.png
text_data.color: red
content: (some red text)
```
but this can become repetitive when we are writing many subtitles. The solution is to use the `styles.yml` file, which will store commonly used styles as key-value pairs, where the key is the "style ID". One such style that stores the data of the above subtitle is
```
- style_id: red
  text_data:
    color: red
```
Then, the `content` key can be replaced with the ID of the style we want to use, and the draft is thus simplified to
```
image_id: 1.png
red: (some red text)
```
> For more information on the `styles.yml` file see [here](style_file.md).

## Hide an Image
Sometimes you do not want to subtitle every image.
```
image_id: 1.png
# don't want to subtitle this

image_id: 2.png
# want to subtitle this
```
The `hide:` key can be used to prevent an image from being subtitled and saved to the output.
```
image_id: 1.png
# don't want to subtitle this
hide:

image_id: 2.png
# want to subtitle this
content: (some content)
```

## Duplicate an Image
If you want to create multiple, consecutive copies of the same image (and subtitle them differently), you can use the `sep:` key.
```
image_id: 1.png
content: (some content)

sep:
content: (some content on copy of 1.png)
```
The duplicated, subtitled images will be suffixed accordingly in the output.
```
# output/[draft]
- 1-1.png # contains (some content)
- 1-2.png # contains (some content on copy of 1.png)
```