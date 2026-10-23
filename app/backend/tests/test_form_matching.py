import base64
import io

import pytest
from PIL import Image, ImageDraw

from form_matching import FormMatchError, compare_form_images


def png_data_url(kind='diagonal'):
    image = Image.new('RGB', (80, 80), 'white')
    draw = ImageDraw.Draw(image)
    if kind == 'diagonal':
        draw.line((15, 15, 60, 60), fill='black', width=5)
    elif kind == 'corner':
        draw.line((15, 15, 60, 15), fill='black', width=5)
        draw.line((15, 15, 15, 60), fill='black', width=5)
    elif kind == 'extra_mark':
        draw.line((15, 15, 60, 60), fill='black', width=5)
        draw.ellipse((55, 10, 64, 19), fill='black')
    buffer = io.BytesIO()
    image.save(buffer, format='PNG')
    return 'data:image/png;base64,' + base64.b64encode(buffer.getvalue()).decode('ascii')


def test_identical_form_images_have_full_mask_overlap_and_zero_centroid_gap():
    result = compare_form_images(png_data_url(), png_data_url(), size=64)

    assert result['available'] is True
    assert result['scored'] is False
    assert result['measurements']['maskIou'] == pytest.approx(1.0)
    assert result['measurements']['centroidDistance'] == pytest.approx(0.0)
    assert result['errors'] == []


def test_visibly_different_synthetic_forms_produce_lower_overlap_measurement():
    matching = compare_form_images(png_data_url(), png_data_url(), size=64)
    different = compare_form_images(png_data_url(), png_data_url('corner'), size=64)

    assert different['measurements']['maskIou'] < matching['measurements']['maskIou']
    assert different['measurements']['centroidDistance'] > 0


def test_extra_mark_changes_form_measurements_without_assigning_error_code():
    result = compare_form_images(png_data_url(), png_data_url('extra_mark'), size=64)

    assert result['measurements']['maskIou'] < 1
    assert result['errors'] == []


def test_rejects_invalid_mask_threshold():
    with pytest.raises(FormMatchError, match='threshold'):
        compare_form_images(png_data_url(), png_data_url(), threshold=256)
