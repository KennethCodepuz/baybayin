import base64
import io
import json
from copy import deepcopy
from pathlib import Path
import sys

from PIL import Image, ImageDraw

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'app' / 'backend'))
from model_features import _feature_measurements
from model_multioutput import validate_multioutput_features

expert = json.loads((ROOT / 'expert reference' / 'expert_.A.json').read_text(encoding='utf-8'))
sample = json.loads((ROOT / 'dataset' / 'W01' / 'A' / 'conformed.json').read_text(encoding='utf-8'))
model = json.loads((ROOT / 'model-artifacts' / 'provisional-20261028' / 'multioutput-run-seed-20261028' / 'multioutput-deployment-model.json').read_text(encoding='utf-8'))

def rendered(record, width, dx=0, dy=0):
    result = deepcopy(record)
    for event in result['events']:
        event['x'] += dx
        event['y'] += dy
    image = Image.new('RGB', (result['canvas']['width'], result['canvas']['height']), 'white')
    draw = ImageDraw.Draw(image)
    previous = None
    for event in result['events']:
        point = (event['x'], event['y'])
        if event['type'] == 'down':
            previous = point
        if previous is not None:
            draw.line((previous, point), fill='#1b2a20', width=width)
            x, y = point
            radius = width / 2
            draw.ellipse((x-radius, y-radius, x+radius, y+radius), fill='#1b2a20')
        previous = None if event['type'] == 'up' else point
    output = io.BytesIO()
    image.save(output, format='PNG')
    result['image'] = 'data:image/png;base64,' + base64.b64encode(output.getvalue()).decode('ascii')
    return result

for name, source in [('expert_path', expert), ('w01_path', sample)]:
    for width, dx, dy in [(2,0,0),(6,0,0),(12,0,0),(24,0,0),(6,40,30)]:
        record = rendered(source, width, dx, dy)
        features = {'target': 'a', **_feature_measurements(expert, record)}
        result = validate_multioutput_features(model, features)
        print(json.dumps({'path': name, 'width': width, 'offset': [dx, dy],
                          'iou': features['mask_iou'], 'dtw': features['stroke_path_distance'],
                          'endpoints': features['start_end_displacement'],
                          'form_vote': result['validation']['form']['confidence'],
                          'count_vote': result['validation']['count']['confidence'],
                          'process_vote': result['validation']['process']['confidence'],
                          'form': result['validation']['form']['state'],
                          'count': result['validation']['count']['state'],
                          'process': result['validation']['process']['state'],
                          'overall': result['overall']['state']}))
