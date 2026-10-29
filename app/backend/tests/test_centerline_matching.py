import base64
import io

import pytest
from PIL import Image, ImageDraw

from centerline_matching import compare_centerlines


def line_image(width, offset=0, extra=False):
    image = Image.new('RGB', (180, 180), 'white')
    draw = ImageDraw.Draw(image)
    draw.line((30 + offset, 40 + offset, 130 + offset, 140 + offset), fill='black', width=width)
    if extra:
        draw.line((60 + offset, 15 + offset, 90 + offset, 15 + offset), fill='black', width=width)
    buffer = io.BytesIO()
    image.save(buffer, format='PNG')
    return 'data:image/png;base64,' + base64.b64encode(buffer.getvalue()).decode('ascii')


def test_centerline_comparison_is_less_sensitive_to_width_and_translation():
    reference = line_image(5)
    matching = compare_centerlines(reference, line_image(5))
    thick = compare_centerlines(reference, line_image(15))
    shifted = compare_centerlines(reference, line_image(5, offset=20))

    assert matching['symmetric_distance'] == pytest.approx(0)
    assert thick['symmetric_distance'] < 0.04
    assert shifted['symmetric_distance'] == pytest.approx(0)


def test_centerline_comparison_retains_disconnected_extra_mark():
    reference = line_image(5)
    same = compare_centerlines(reference, reference)
    extra = compare_centerlines(reference, line_image(5, extra=True))

    assert extra['symmetric_distance'] > same['symmetric_distance']
