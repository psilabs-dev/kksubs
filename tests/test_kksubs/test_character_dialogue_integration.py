"""Integration tests for character/dialogue rendering workflow."""
import tempfile
import os
from PIL import Image
from kksubs.controller.subtitle import SubtitleController


def generate_test_image(directory, image_name):
    """Generate a test image in the specified directory."""
    image = Image.new('RGB', (1920, 1080), (255, 255, 255))
    image_path = os.path.join(directory, image_name)
    image.save(image_path)
    image.close()


def test_character_dialogue_rendering_workflow():
    """Test end-to-end character/dialogue subtitle rendering."""
    with tempfile.TemporaryDirectory() as test_dir:
        # Create controller
        controller = SubtitleController(test_dir)
        controller.create()

        # Generate test image
        image_dir = controller.get_image_directory()
        generate_test_image(image_dir, 'scene1.png')

        # Create styles.yml with character/dialogue style
        styles_content = """
- style_id: shakespeare
  character_dialogue:
    enabled: true
    character_name: "Shakespeare"
    separator: ": "
    character:
      text_data:
        color: [255, 215, 0]
        size: 24
      outline_data:
        color: [0, 0, 0]
        size: 2
    dialogue:
      text_data:
        color: [255, 255, 255]
        size: 20
      outline_data:
        color: [0, 0, 0]
        size: 2
  box_data:
    grid10: [5, 5]
    align_h: center
    align_v: center

- style_id: narrator
  text_data:
    color: [200, 200, 200]
    size: 18
  box_data:
    grid10: [5, 1]
    align_h: center
    align_v: top
"""
        styles_path = os.path.join(controller.workspace_directory, 'styles.yml')
        with open(styles_path, 'w') as f:
            f.write(styles_content)

        # Create draft with character/dialogue
        scripts_dir = controller.get_scripts_directory()
        draft_files = os.listdir(scripts_dir)
        assert len(draft_files) == 1
        draft_path = os.path.join(scripts_dir, draft_files[0])

        draft_content = """
image_id: scene1.png
narrator: Once upon a time...
shakespeare: To be or not to be,
that is the question
"""
        with open(draft_path, 'w') as f:
            f.write(draft_content)

        # Run subtitle generation
        controller.add_subtitles(allow_multiprocessing=False)

        # Verify output
        output_dir = controller.get_output_directory_by_script(draft_files[0])
        assert os.path.exists(output_dir)
        output_files = os.listdir(output_dir)
        assert 'scene1.png' in output_files

        # Verify output image exists and has reasonable size
        output_image_path = os.path.join(output_dir, 'scene1.png')
        assert os.path.exists(output_image_path)
        output_image = Image.open(output_image_path)
        assert output_image.size == (1920, 1080)
        output_image.close()


def test_mixed_subtitle_types_workflow():
    """Test workflow with both regular and character/dialogue subtitles."""
    with tempfile.TemporaryDirectory() as test_dir:
        controller = SubtitleController(test_dir)
        controller.create()

        # Generate test image
        image_dir = controller.get_image_directory()
        generate_test_image(image_dir, 'scene2.png')

        # Create styles.yml
        styles_content = """
- style_id: character1
  character_dialogue:
    enabled: true
    character_name: "Alice"
    character:
      text_data:
        color: [255, 100, 100]
        size: 22
    dialogue:
      text_data:
        color: [255, 255, 255]
        size: 18

- style_id: regular_style
  text_data:
    color: [150, 150, 150]
    size: 16
"""
        styles_path = os.path.join(controller.workspace_directory, 'styles.yml')
        with open(styles_path, 'w') as f:
            f.write(styles_content)

        # Create draft with mixed subtitle types
        scripts_dir = controller.get_scripts_directory()
        draft_files = os.listdir(scripts_dir)
        draft_path = os.path.join(scripts_dir, draft_files[0])

        draft_content = """
image_id: scene2.png
content: (A regular subtitle appears)
character1: Hello, world!
"""
        with open(draft_path, 'w') as f:
            f.write(draft_content)

        # Run subtitle generation
        controller.add_subtitles(allow_multiprocessing=False)

        # Verify output
        output_dir = controller.get_output_directory_by_script(draft_files[0])
        output_image_path = os.path.join(output_dir, 'scene2.png')
        assert os.path.exists(output_image_path)

        # Verify image can be opened (basic validation)
        output_image = Image.open(output_image_path)
        assert output_image.size == (1920, 1080)
        output_image.close()


def test_missing_font_size_rendering():
    """Test that missing font size does not crash rendering."""
    with tempfile.TemporaryDirectory() as test_dir:
        controller = SubtitleController(test_dir)
        controller.create()

        image_dir = controller.get_image_directory()
        generate_test_image(image_dir, 'bug_repro.png')

        styles_content = """
- style_id: buggy_style
  character_dialogue:
    enabled: true
    character_name: "Buggy"
    character:
      text_data:
        color: [255, 0, 0]
    dialogue:
      text_data:
        color: [0, 255, 0]
"""
        styles_path = os.path.join(controller.workspace_directory, 'styles.yml')
        with open(styles_path, 'w') as f:
            f.write(styles_content)

        scripts_dir = controller.get_scripts_directory()
        draft_files = os.listdir(scripts_dir)
        draft_path = os.path.join(scripts_dir, draft_files[0])

        draft_content = """
image_id: bug_repro.png
buggy_style: Text content
"""
        with open(draft_path, 'w') as f:
            f.write(draft_content)

        # Should not crash and SHOULD render something (not return original image)
        controller.add_subtitles(allow_multiprocessing=False)

        output_dir = controller.get_output_directory_by_script(draft_files[0])
        output_image_path = os.path.join(output_dir, 'bug_repro.png')
        assert os.path.exists(output_image_path)
        
        # Verify that the image was actually modified (subtitles rendered)
        # If the bug exists, it returns the original image, so this should fail.
        # We need to compare pixel data or similar.
        output_image = Image.open(output_image_path)
        input_image = Image.open(os.path.join(image_dir, 'bug_repro.png'))
        
        # Simple check: different content
        assert list(output_image.getdata()) != list(input_image.getdata()), "Output image is identical to input, implying render failure."
        
        output_image.close()
        input_image.close()
