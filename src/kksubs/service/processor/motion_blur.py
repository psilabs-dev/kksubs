import numpy as np
import cv2
from PIL import Image

from kksubs.service.processor.utils.image import in_cv2_environment

def apply_horizontal_blur(image, kernel_size=None):
    if kernel_size is None:
        kernel_size = 50
    kernel = np.zeros((kernel_size, kernel_size))
    kernel[int((kernel_size - 1)/2), :] = np.ones(kernel_size)
    kernel /= kernel_size
    horizontally_blurred_image = cv2.filter2D(image, -1, kernel)
    return horizontally_blurred_image

def apply_vertical_blur(image, kernel_size=None):
    if kernel_size is None:
        kernel_size = 50
    kernel = np.zeros((kernel_size, kernel_size))
    kernel[:,int((kernel_size - 1)/2)] = np.ones(kernel_size)
    kernel /= kernel_size
    vertically_blurred_image = cv2.filter2D(image, -1, kernel)
    return vertically_blurred_image

def get_sup_kernel_size(kernel_size):
    parity = kernel_size%2
    # must be odd.
    result = int(np.ceil(np.sqrt(2)*kernel_size))
    if result%2==parity:
        return result
    return result+1

# get the nxn submatrix from an NxN matrix (starting from the center).
# assume n, N are odd, and N-n > 0.
# (N-n)/2 is the diff.
def get_center_submatrix(super_matrix, n, N=None):
    if N is None:
        N = len(super_matrix)
    difference = int((N-n)/2)
    return super_matrix[difference:difference+n, difference:difference+n]


def apply_motion_blur(image:Image.Image, kernel_size=None, angle=None) -> Image.Image:
    if kernel_size is None or kernel_size == 0:
        return image
    if angle is None:
        angle = 0
    if angle%180==0:
        return in_cv2_environment(apply_horizontal_blur)(image, kernel_size=kernel_size)
    if angle%180==90:
        return in_cv2_environment(apply_vertical_blur)(image, kernel_size=kernel_size)

    if kernel_size%2==0:
        # warn that kernel size is even, will be incremented so it is odd.
        kernel_size += 1
    # convert image to cv2
    cv2_image = np.array(image.convert("RGB"))[:,:,::-1].copy()

    sup_kernel_size = get_sup_kernel_size(kernel_size)
    # print(sup_kernel_size)
    sup_kernel = np.zeros((sup_kernel_size, sup_kernel_size))
    sup_kernel[int((sup_kernel_size-1)/2), :] = np.ones(sup_kernel_size)
    sup_kernel = sup_kernel * 255
    sup_kernel_as_image = Image.fromarray(sup_kernel)
    rotated_sup_kernel = sup_kernel_as_image.rotate(angle)
    rotated_sup_kernel = np.asarray(rotated_sup_kernel)
    rotated_kernel = get_center_submatrix(rotated_sup_kernel, kernel_size, sup_kernel_size)/255/kernel_size
    rotated_mb = cv2.filter2D(cv2_image, -1, rotated_kernel)
    blurred_image = Image.fromarray(cv2.cvtColor(rotated_mb, cv2.COLOR_BGR2RGB))
    # convert cv2 to image.
    return blurred_image