from .utils import ask_string, ask_multichoice
import numpy as np
import flowvid as fv


def preset_flow_arrows():
    # Flow files and RGB frames of video
    flo_dir = ask_string('Flow files directory ({s}): ', default='flo')

    # Background settings
    use_flow = ask_multichoice('Use flow colors for image? ({s}): ',
                               answer_map={'yes': True, 'no': False}, default='no')
    if use_flow:
        arrow_color = [0, 0, 0]
    else:
        arrow_color = 'flow'
        rgb_dir = ask_string('Image directory ({s}): ', default='png')

    # Arrow subsampling
    subsample_ratio = int(ask_string(
        'Flow subsample ratio ({s}): ', default='5'))

    # Output options
    framerate = int(ask_string('Video framerate ({s}): ', default='24'))

    # Add points and generate image
    flo_data = fv.input.flo(flo_dir)
    if use_flow:
        flo_data_norm = fv.normalize_frame(flo_data)
        rgb_data = fv.flow_to_rgb(flo_data_norm)
        flat_colors = True
    else:
        rgb_data = fv.input.rgb(rgb_dir)
        flat_colors = False
    arrow_data = fv.draw_flow_arrows(rgb_data, flo_data, color=arrow_color,
                                     flat_colors=flat_colors, subsample_ratio=subsample_ratio, ignore_ratio_warning=False)

    # Generate output
    out = fv.output.show_plot(
        title='flow_arrows result', framerate=framerate)
    out.show_all(arrow_data, show_count=True)