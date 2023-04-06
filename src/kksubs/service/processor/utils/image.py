from PIL import Image
import cv2
import numpy as np

def cv2_to_pil(cv2_image):
    return Image.fromarray(cv2.cvtColor(cv2.convertScaleAbs(cv2_image), cv2.COLOR_BGRA2RGBA))
    # return Image.fromarray(cv2.cvtColor(cv2.convertScaleAbs(cv2_image), cv2.COLOR_BGRA2RGBA))
def pil_to_cv2(pil_image):
    # return cv2.cvtColor(np.array(pil_image), cv2.COLOR_BGRA2RGBA)
    return cv2.cvtColor(np.array(pil_image), cv2.COLOR_BGRA2RGB)

def in_cv2_environment(fn):
    # creates a cv2 environment for a cv2-valued function.
    def decorated_fn(image, *args, **kwargs):
        return cv2_to_pil(fn(pil_to_cv2(image), *args, **kwargs))
    return decorated_fn