
# All this code is adapted from the one available at:
# https://people.csail.mit.edu/celiu/OpticalFlow/
# which uses the following color circle idea:
# http://www.quadibloc.com/other/colint.htm

import numpy as np


def make_color_wheel():
    # how many hues ("cols") separate each color
    # (for this color wheel)
    RY = 15  # red-yellow
    YG = 6   # yellow-green
    GC = 4   # green-cyan
    CB = 11  # cyan-blue
    BM = 13  # blue-magenta
    MR = 6   # magenta-red

    ncols = RY + YG + GC + CB + BM + MR
    colorwheel = np.zeros((ncols, 3), dtype=np.uint8)  # r g b

    col = 0
    # RY
    colorwheel[col:col+RY, 0] = 255
    colorwheel[col:col+RY, 1] = np.floor(255*np.arange(RY)/RY)
    col = col + RY
    # YG
    colorwheel[col:col+YG, 0] = np.ceil(255*np.arange(YG, 0, -1)/YG)
    colorwheel[col:col+YG, 1] = 255
    col = col + YG
    # GC
    colorwheel[col:col+GC, 1] = 255
    colorwheel[col:col+GC, 2] = np.floor(255*np.arange(GC)/GC)
    col = col + GC
    # CB
    colorwheel[col:col+CB, 1] = np.ceil(255*np.arange(CB, 0, -1)/CB)
    colorwheel[col:col+CB, 2] = 255
    col = col + CB
    # BM
    colorwheel[col:col+BM, 2] = 255
    colorwheel[col:col+BM, 0] = np.floor(255*np.arange(BM)/BM)
    col = col + BM
    # MR
    colorwheel[col:col+MR, 2] = np.ceil(255*np.arange(MR, 0, -1)/MR)
    colorwheel[col:col+MR, 0] = 255

    return colorwheel


def uv_to_rgb(fu, fv):
    if fu.ndim < 3:
        raise AssertionError(
            'Flow vectors must have (frame, height, width) shape')

    colorwheel = make_color_wheel()
    ncols = colorwheel.shape[0]

    [nframes, h, w] = fu.shape
    rgb = np.empty([nframes, h, w, 3], dtype=np.uint8)

    for frame, (u, v) in enumerate(zip(fu, fv)):
        rad = np.sqrt(u ** 2 + v ** 2)
        a = np.arctan2(-v, -u) / np.pi
        fk = (a + 1.0) / 2.0 * (ncols - 1.0) + 1.0  # -1~1 mapped to 1~ncols
        k0 = fk.astype(np.uint8)
        k1 = (k0 + 1) % ncols
        f = fk - k0
        for i in range(3):  # r g b
            col0 = colorwheel[k0, i]/255.0
            col1 = colorwheel[k1, i]/255.0
            col = np.multiply(1.0-f, col0) + np.multiply(f, col1)

            # increase saturation with radius
            col = np.multiply(1.0 - rad, 1.0 - col)

            rgb[frame, :, :, i] = np.floor(col * 255.0)

    return rgb
