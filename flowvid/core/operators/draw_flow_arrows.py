import matplotlib.pyplot as plt
import numpy as np
import math
from ..filterable import Filterable
from ..util.convert_to_axes import convert_to_axes
from ..util.color_flow import flow_to_rgb
from .base_operator import Operator


class DrawFlowArrows(Operator):
    """
        Given a list of images and flow data, draw a visual representation
        of the flow using arrows on top of the image
    """

    def __init__(self, image_data, flow_data, color, flat_colors, subsample_ratio, ignore_ratio_warning):
        if not isinstance(image_data, Filterable):
            raise AssertionError(
                'image_data should contain a list of rgb data')
        if not isinstance(flow_data, Filterable):
            raise AssertionError(
                'flow_data should contain a list of flow data')
        if (not isinstance(color, list) or len(color) != 3) and color != 'flow':
            raise AssertionError(
                'color should be a [r, g, b] list where rgb range from 0 to 255, or \'flow\' for flow colors.')
        image_data.assert_type('rgb', 'figure')
        flow_data.assert_type('flo')

        if subsample_ratio < 1:
            raise AssertionError(
                'subsample_ratio should be a positive integer but it is {n}.'.format(n=subsample_ratio))
        Operator.__init__(self)
        self._image_data = image_data
        self._flow_data = flow_data
        self._color = color
        self._flat_colors = flat_colors

        [h, w] = flow_data[0].shape[0:2]
        self._subsample_x = subsample_ratio
        self._subsample_y = subsample_ratio
        if (subsample_ratio % h != 0 or subsample_ratio % w != 0) and not ignore_ratio_warning:
            rem_w = (w % subsample_ratio) / (w // subsample_ratio)
            rem_h = (h % subsample_ratio) / (h // subsample_ratio)
            self._subsample_x = subsample_ratio + rem_w
            self._subsample_y = subsample_ratio + rem_h
            print('Warning: subsample_ratio resized from ({o}, {o}) to ({nx}, {ny}) to fit image size of ({w}, {h})\nYou can try to fix it by modifying subsample_ratio parameter\n'.format(
                o=subsample_ratio, nx=self._subsample_x, ny=self._subsample_y, w=w, h=h))
        self._arrow_width = subsample_ratio / 20.0

    def _items(self):
        return (self._draw(image, flow, self._color) for image, flow in zip(self._image_data, self._flow_data))

    def __len__(self):
        return min(len(self._image_data), len(self._flow_data))

    def get_type(self):
        return 'figure'

    @staticmethod
    def _mean_flow(flow, px, py, qx, qy):
        """ qx > px, qy > py and all inside flow bounds """
        pyc = math.ceil(py)
        pxc = math.ceil(px)
        qyf = math.floor(qy)
        qxf = math.floor(qx)

        # inside the rectangle
        total_sum = np.sum(flow[pyc:qyf, pxc:qxf, :], axis=(0, 1))
        total_area = (qyf - pyc) * (qxf - pxc)

        # rectangle's border might not be exact to pixel edges
        # add to total_area and sum
        rem_px = 1.0 - (px - int(px))
        rem_py = 1.0 - (py - int(py))
        rem_qx = qx - int(qx)
        rem_qy = qy - int(qy)
        # left edge
        if rem_px < 1:
            total_area += (qyf - pyc) * rem_px
            total_sum += np.sum(flow[pyc:qyf, pxc-1, :], axis=(0, 1)) * rem_px
            # top-left edge
            if rem_py < 1:
                total_area += rem_py * rem_px
                total_sum += flow[int(py), int(px), :] * rem_py * rem_px
        # top edge
        if rem_py < 1:
            total_area += (qxf - pxc) * rem_py
            total_sum += np.sum(flow[pyc-1, pxc:qxf, :], axis=(0, 1)) * rem_py
            # top-right edge
            if rem_qx > 0:
                total_area += rem_qx * rem_py
                total_sum += flow[int(py), int(qx) + 1, :] * rem_qx * rem_py
        # right-edge
        if rem_qx > 0:
            total_area += (qyf - pyc) * rem_qx
            total_sum += np.sum(flow[pyc:qyf, qxf+1, :], axis=(0, 1)) * rem_qx
            # bottom-right edge
            if rem_qy > 0:
                total_area += rem_qy * rem_qx
                total_sum += flow[int(qy)+1, int(qx)+1, :] * rem_qy * rem_qx
        # bottom edge
        if rem_qy > 0:
            total_area += (qxf - pxc) * rem_qy
            total_sum += np.sum(flow[qyf+1, pxc:qxf, :], axis=(0, 1)) * rem_qy
            # bottom-left edge
            if rem_px < 1:
                total_area += rem_px * rem_qy
                total_sum += flow[int(py), int(qy)+1, :] * rem_px * rem_qy

        return total_sum / total_area

    def _draw(self, image, flow, color):
        ax = convert_to_axes(image)

        [h, w] = flow.shape[0:2]
        ix = int(w // self._subsample_x)
        iy = int(h // self._subsample_y)
        arrows = np.zeros((iy, ix, 2))

        for y in range(iy):
            for x in range(ix):
                # flow zone
                px = x * self._subsample_x
                py = y * self._subsample_y
                qx = px + self._subsample_x
                qy = py + self._subsample_y
                # get mean flow in zone
                arrows[y, x, :] = DrawFlowArrows._mean_flow(
                    flow, px, py, qx, qy)

        if self._color == 'flow':
            fu = arrows[:, :, 0]
            fv = arrows[:, :, 1]
            arrows_norm = np.copy(arrows) / np.sqrt(fu ** 2 + fv ** 2).max()
            flow_colors = flow_to_rgb(arrows_norm)

        if not self._flat_colors:
            fu = arrows[:, :, 0]
            fv = arrows[:, :, 1]
            max_module = (fu ** 2 + fv ** 2).max()

        # TODO vectorize/improve arrow draw method
        for y in range(iy):
            for x in range(ix):
                # arrow origin
                ox = (x + 0.5) * self._subsample_x
                oy = (y + 0.5) * self._subsample_y
                # arrow length
                [dx, dy] = arrows[y, x]
                # arrow color
                if self._color == 'flow':
                    color = flow_colors[y, x, :]
                else:
                    color = self._color
                # arrow color attenuation
                if not self._flat_colors:
                    color = color * math.sqrt((dx ** 2 + dy ** 2) / max_module)
                # convert to RGBA (for color argument)
                color = (color[0] / 255.0, color[1] /
                         255.0, color[2] / 255.0, 1.0)
                # draw arrow
                ax.arrow(ox, oy, dx, dy, color=color,
                         width=self._arrow_width, length_includes_head=True)

        return ax