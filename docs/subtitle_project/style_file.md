# The `styles.yml` file

A "style" stores data that describes a subtitle's content, for example its font, font size, color, etc. The `styles.yml` file stores these styles in a key/value pair. The style of a subtitle in a draft can then be described with a style ID that references a specific style in the `styles.yml` file.

Then rather than styling a subtitle in the draft itself:
```yaml
text_data.size: 12
box_data.align_h: center
content: This is some text
```
One can declare the style in the `styles.yml` file:
```yaml
- style_id: c12
  text_data:
    size: 12
  box_data:
    align_h: center
```
And reference the style's key to automatically style the text:
```yaml
c12: This is some text
```

### Style Inheritance
Properties of styles can be inherited using the syntax, and their properties can be overridden.
```yaml
- style_id: white-text
  text_data:
    color: white
    size: 30
- style_id: larger-white-text(white-text)
  text_data:
    size: 40
```
In this block, the `large-white-text` style assigns the same font color to a subtitle as its parent, but assigns a font size of 40 instead of 30.

Multiple and nested inheritance is allowed.
```yaml
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

## Multiple Inheritance

> Note: experimental and subject to change.

As discussed previously, inheritance is used to automate the configuration of styles.

Instead of a regular style object, we have a *matrix* to express inheritance.
```yaml
# normal inheritance
- style_id: style-1
- style_id: style-2
- style_id: style-2-style-1(style-2, style-1)

# matrix inheritance
- matrix:
  - row:
      styles:
      - style_id: style-1
  - row:
      styles:
      - style_id: style-2
```
### Example

Using a 'matrix' format, configure more styles quickly:


```yaml
# styles.yml
- matrix:
  # first row
  - row:
      styles:
      - style_id: style-1
      - style_id: style-2
  # second row
  - row:
      styles:
      - style_id: style-3
      - style_id: style-4
      - style_id: style-5
```
The matrix contains 2 *rows*, the first with styles 1 and 2, and the second with styles 3-5. Multiple rows of arbitrary lengths can be composed together.

```yaml
- matrix:
  - row-1
  - row-2
  - ...
  - row-n
```

When `kksubs` compiles the styles folder, it will also multiply each row of styles together, where multiplication is style inheritance. Since order matters for inheritance, it also matters which row goes first.

The above is the same as adding the following 11 styles by hand:
```yaml
- style_id: style-1
- style_id: style-2
- ...
- style_id: style-5
- style_id: style-3-style-1(style-3, style-1)
- style_id: style-3-style-2(style-3, style-2)
- style_id: style-4-style-1(style-4, style-1)
- ...
- style_id: style-5-style-1(style-5, style-1)
- style_id: style-5-style-2(style-5, style-2)
```
Several common rows are built-in. For example, the `grid4` configurations
```yaml
- style_id: "00"
  box_data:
    grid4: [0, 0]
- style_id: "01"
  box_data:
    grid4: [0, 1]
- ...
- style_id: "44"
  box_data:
    grid4: [4, 4]
```
are represented by the `grid4_complete` row ID.
```yaml
- matrix:
  - row: 
      row_id: grid4_complete
  - row:
      styles:
      - style_id: character
# creates styles character-11, character-12, ...,
```
The delimiter can be controlled using "context" layers, thereby removing the "`-`" between style IDs.
```
  - row: 
      row_id: grid4_complete
  - context:
      delimiter: ''
  - row:
      styles:
      - style_id: character
```