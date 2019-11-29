import sys
import numpy as np
from numpy import genfromtxt
from flowvid.input.flodata import FloData
from flowvid.input.rgbdata import RGBData
from flowvid.filter.basefilter import Filter
from flowvid.filter.normalize import NormalizeFrame, NormalizeVideo
from flowvid.filter.drawrectangle import DrawRectangle
from flowvid.operator.baseoperator import Operator
from flowvid.operator.addflow import AddFlow
from flowvid.filter.flotorgb import FloToRGB
from flowvid.output.videooutput import VideoOutput


def ask_string(format_prompt, default):
    answer = input(format_prompt.format(s='default: ' + default))
    if answer:
        return answer
    else:
        return default


def ask_multichoice(format_prompt, answer_map, default):
    keys = map(lambda a: '['+a+']' if a == default else a, answer_map.keys())
    answer = input(format_prompt.format(s=', '.join(keys)))
    if answer in answer_map:
        return answer_map[answer]
    else:
        return answer_map[default]


video_type = sys.argv[1] if len(sys.argv) > 0 else ''
if video_type == 'color':

    flo_dir = ask_string('Flow files directory ({s}): ', default='flo')
    norm_type = ask_multichoice('Vector normalize type ({s}): ',
                                answer_map={'video': 'video', 'frame': 'frame', 'none': None}, default='frame')
    framerate = int(ask_string('Video framerate ({s}): ', default='24'))
    out_name = ask_string(
        'Output video name ({s}): ', default='output_flo.mp4')

    flodata = FloData.from_directory(flo_dir)
    datafilter = Filter()
    if norm_type == 'frame':
        datafilter = NormalizeFrame()
    elif norm_type == 'video':
        datafilter = NormalizeVideo(flodata, clamp_pct=0.8, gamma=0.7)
    out = VideoOutput(filename=out_name, framerate=framerate)
    rgbfilter = FloToRGB()
    for i, flow in enumerate(flodata):
        print('Frame', i)
        out.add_frame(rgbfilter.apply(datafilter.apply(flow)))

elif video_type == 'add':    

    flo_dir = 'test/flo'#ask_string('Flow files directory ({s}): ', default='flo')
    image = 'test/png/0000.png'
    n = 10
    framerate = 1
    out_name = 'output.mp4'

    flodata = FloData.from_directory(flo_dir, 0, n)
    imdata = next(iter(RGBData.from_file(image)))
    addoperator = AddFlow(imdata.shape[0:2])
    out = VideoOutput(filename=out_name, framerate=framerate)
    out.add_frame(imdata)
    for i, flow in enumerate(flodata):
        print('Frame', i)
        imdata = addoperator.apply(imdata, flow)
        out.add_frame(imdata)

elif video_type == 'rectangle_truth':

    flo_dir = 'test/flo'#ask_string('Flow files directory ({s}): ', default='flo')
    png_dir = 'test/png'
    track = 'test/track/video10_annot.txt'
    framerate = 8
    out_name = 'output_truth.mp4'

    pngdata = RGBData.from_directory(png_dir, num_files=600)
    drawrec = DrawRectangle()
    recdata = genfromtxt(track, delimiter=' ')
    print(recdata.shape)

    out = VideoOutput(filename=out_name, framerate=framerate)

    for i, image in enumerate(pngdata):
        print('Frame', i)
        if recdata[i, 0] != -1:
            x = int(recdata[i, 0])
            y = int(recdata[i, 1])
            wx = int(recdata[i, 2])
            wy = int(recdata[i, 3])
            image = drawrec.apply(image, [0, 255, 0], x, y, wx, wy)
        out.add_frame(image)

elif video_type == 'rectangle_flo':

    flo_dir = 'test/flo'#ask_string('Flow files directory ({s}): ', default='flo')
    png_dir = 'test/png'
    track = 'test/track/video10_annot.txt'
    framerate = 8
    out_name = 'output_flo.mp4'

    pngdata = RGBData.from_directory(png_dir, first=335, num_files=100)
    flodata = FloData.from_directory(flo_dir, first=335, num_files=100)
    drawrec = DrawRectangle()
    rec = genfromtxt(track, delimiter=' ')[0,:]
    x0 = rec[0]
    y0 = rec[1]
    x1 = x0 + rec[2]
    y1 = y0 + rec[3]

    out = VideoOutput(filename=out_name, framerate=framerate)
    for i, (flow, image) in enumerate(zip(flodata, pngdata)):
        print('Frame', i)
        x0 += flow[int(y0), int(x0), 0]
        y0 += flow[int(y0), int(x0), 1]
        x1 += flow[int(y1), int(x1), 0]
        y1 += flow[int(y1), int(x1), 1]
        image = drawrec.apply(image, [255, 0, 0], int(x0), int(y0), int(x1 - x0), int(y1 - y0))
        out.add_frame(image)

else:
    print('Need parameter: {{ color | add | rectangle_truth | rectangle_flo }}'.format(p=sys.argv[0]))
