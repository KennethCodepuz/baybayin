import json
import sys
from pathlib import Path

root = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(root / 'app' / 'backend'))
from model_multioutput import validate_sample_with_model
from robustness_experiment import render

reference_root = root / 'expert reference'
old_path = root / 'model-artifacts/provisional-20261028/multioutput-run-seed-20261028/multioutput-deployment-model.json'
new_path = root / 'model-artifacts/provisional-20261028/centerline-pilot/multioutput-deployment-model.json'
samples = {
    'expert': json.loads((reference_root / 'expert_.A.json').read_text(encoding='utf-8')),
    'W01': json.loads((root / 'dataset/W01/A/conformed.json').read_text(encoding='utf-8')),
}
for name, original in samples.items():
    for width, dx, dy in [(2, 0, 0), (6, 0, 0), (12, 0, 0), (24, 0, 0), (6, 40, 30)]:
        sample = render(original, width, dx, dy)
        old = validate_sample_with_model(sample, old_path, reference_root)
        new = validate_sample_with_model(sample, new_path, reference_root)
        print(json.dumps({
            'sample': name, 'width': width, 'offset': [dx, dy],
            'old_iou': old['evidence']['mask_iou'],
            'new_centerline_distance': 1 - new['evidence']['centerline_similarity'],
            'dtw': new['evidence']['stroke_path_distance'],
            'normalized_endpoint': new['evidence']['normalized_endpoint_displacement'],
            'old_form': old['validation']['form']['state'],
            'new_form': new['validation']['form']['state'],
            'new_count': new['validation']['count']['state'],
            'new_process': new['validation']['process']['state'],
            'new_overall': new['overall']['state'],
        }))
