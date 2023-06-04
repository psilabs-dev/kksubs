# Style Fields
A list of style fields that can be used in the draft.

| style field ID | name | values | description |
| - | - | - | - |
| `text_data.font` | font | "default"<br/>path to a TTF font |
| `text_data.size` | font size | positive int | 
| `text_data.color` | font fill color | color<br/>[int, int, int] | Uses RGB triple, e.g. "red" is [255, 0, 0] |
| `text_data.stroke_size` | font outline size | positive int<br/>0 |
| `text_data.stroke_color` | font outline color | color<br/>[int, int, int] |
| `text_data.alpha` | alpha channel for text | float between 0 and 1 |
| - | - | - |
| `outline_data.color` | text outline color | color<br/>[int, int, int]
| `outline_data.size` | text outline size | positive int<br/>0
| `outline_data.blur` | text outline blur | positive int<br/>0
| `outline_data.alpha` | alpha channel for outline | float between 0 and 1 |
| - | - | - |
| `box_data.align_h` | horizontal alignment | "left"<br/>"right"<br/>"center" |
| `box_data.align_v` | vertical alignment | "bottom"<br/>"top"<br/>"center" |
| `box_data.box_width` | text width | positive int |
| `box_data.anchor` | textbox anchor point | [int, int] | Anchors the subtitle textbox to a point on the image. Default position is the center of the image and nonzero values displace the anchor point from the center.<br/><br/>The anchor's positional relation to the textbox depends on horizontal and vertical alignment. |
| `box_data.grid4` | 4ths grid coordinates | [int, int] | An alternative coordinate system that overrides `box_data.anchor`. Partitions the image into horizontal and vertical fourths, and places the textbox anchor point on one of these points. <br/><br/>[2, 2] = center<br/>[0, 0] = top left<br/>[4, 0] = top right<br/>[0, 4] = bottom left<br/>[4, 4] = bottom right |
| `box_data.grid10` | 10ths grid coordinates | [int, int] |
| `box_data.nudge` | displacement from anchor point | [int, int] | Nudges the textbox from the anchor point.|
| `box_data.rotate` | rotate subtitle | int (degree) | |
| `styles` | sub-styles under the style | List[Style] | Holds "child" style objects that share the anchor point of the parent style. Must be added from `styles.yml`. |

### Notes

* Outline data can be represented in either `outline_data` or `outline_data_1` (which is presented below `outline_data`).

## Effects
In addition to styling the text itself, the `Style` object contains other fields related to adding effects to an image.

| style field ID | name | values | description |
|-|-|-|-|
| `asset.path` | path to image asset | | |
| `asset.rotate` | adjust asset angle | |
| `asset.scale` | adjust asset size | |
| `asset.alpha` | adjust asset alpha channel | |
| `brightness.value` | adjust brightness | positive float | Adjust the brightness of an image. Decrease to lower brightness.<br/>Default is 1 (original brightness).
| `gaussian.value` | apply gaussian blur | positive int<br/>0 | Apply gaussian blur to an image.<br/>Default is 0 (no blur)
| `motion` | motion blur | | Data related to applying motion blur to an image.
| `motion.value` | motion blur strength | positive int<br/>0 | Adjust motion blur strength to an image.<br/>Default is None (no blur)
| `motion.angle` | motion blur angle | range(0, 360) | Adjust line of blur
| `mask.path` | add mask | path | Import an image as a mask for the above effects.
| `background.path` | add background | path | Add an image immediately below the content layer of a subtitled image. Image can be a valid path from the project directory or an absolute path. (not affected by mask)