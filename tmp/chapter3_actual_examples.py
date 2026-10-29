import base64
import io
import json
import sys
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

root = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(root / 'app' / 'backend'))
from form_matching import compare_form_images
from multimodal import extract_stroke_features, normalize_png_data_url
from stroke_matching import compare_stroke_sequences, normalize_stroke_sequence, resample_by_arc_length

expert = json.loads((root / 'expert reference' / 'expert_.A.json').read_text(encoding='utf-8'))
learner = json.loads((root / 'dataset' / 'W01' / 'A' / 'conformed.json').read_text(encoding='utf-8'))
out = root / 'tmp' / 'chapter3-figures'
regular = ImageFont.truetype('C:/Windows/Fonts/arial.ttf', 27)
small = ImageFont.truetype('C:/Windows/Fonts/arial.ttf', 22)
bold = ImageFont.truetype('C:/Windows/Fonts/arialbd.ttf', 33)

def normalized(record):
    url = normalize_png_data_url(record['image'], 128)['pngDataUrl']
    return Image.open(io.BytesIO(base64.b64decode(url.split(',')[1]))).convert('L')

ref, attempt = normalized(expert), normalized(learner)
refmask, testmask = ref.point(lambda p: 255 if p < 240 else 0), attempt.point(lambda p: 255 if p < 240 else 0)
overlap = Image.new('RGB', (128, 128), 'white')
for y in range(128):
    for x in range(128):
        a, b = refmask.getpixel((x, y)) != 0, testmask.getpixel((x, y)) != 0
        overlap.putpixel((x, y), (30, 80, 64) if a and b else (51, 118, 185) if a else (214, 131, 55) if b else (255, 255, 255))
metrics = compare_form_images(expert['image'], learner['image'], size=128)['measurements']
im = Image.new('RGB', (1200, 700), 'white'); d = ImageDraw.Draw(im)
d.text((30, 20), 'Actual image comparison: target A', font=bold, fill='#183b35')
d.text((30, 68), 'Expert reference vs W01 intended-conforming attempt', font=regular, fill='#172c27')
for x, img, title in [(55, ref, 'Expert normalized'), (430, attempt, 'W01 normalized'), (805, overlap, 'Mask overlay')]:
    d.text((x, 140), title, font=regular, fill='#172c27')
    im.paste(img.convert('RGB').resize((320, 320), Image.Resampling.NEAREST), (x, 190))
    d.rectangle((x,190,x+320,510), outline='#9aaea7', width=2)
d.text((45, 545), f"Mask IoU = {metrics['maskIou']:.3f}    |    Threshold = 240 / 255", font=regular, fill='#172c27')
d.text((45, 590), 'Green: both masks   Blue: expert only   Orange: W01 only', font=small, fill='#344b45')
d.text((45, 630), 'Normalized to 128 × 128; masks use the same processing as pilot-v1.', font=small, fill='#344b45')
im.save(out / 'actual-mask.png')

left = extract_stroke_features(expert)['strokes']; right = extract_stroke_features(learner)['strokes']
comparison = compare_stroke_sequences([s['points'] for s in left], [s['points'] for s in right])
item = next(x for x in comparison['comparisons'] if x['comparisonType'] == 'dtw_path')
idx = item['strokeIndex']
norm_left = normalize_stroke_sequence([s['points'] for s in left])[idx]
norm_right = normalize_stroke_sequence([s['points'] for s in right])[idx]
a, b = resample_by_arc_length(norm_left, 32), resample_by_arc_length(norm_right, 32)
im = Image.new('RGB', (1200, 850), 'white'); d = ImageDraw.Draw(im)
d.text((30, 20), 'Actual DTW stroke alignment: target A', font=bold, fill='#183b35')
d.text((30, 70), f'Expert reference vs W01 intended-conforming, stroke {idx + 1}', font=regular, fill='#172c27')
def xy(p, left, top): return (left + p['x'] * 420, top + p['y'] * 420)
for pos, points, label, color in [(45, a, 'Expert stroke', '#276b57'), (690, b, 'W01 stroke', '#a65e20')]:
    d.text((pos, 125), label, font=regular, fill='#172c27')
    d.rectangle((pos, 175, pos+420, 595), outline='#b3c4bc', width=2)
    coords=[xy(p,pos,175) for p in points]
    d.line(coords, fill=color, width=5)
    for x,y in coords: d.ellipse((x-4,y-4,x+4,y+4), fill=color)
for n,(i,j) in enumerate(item['alignmentPath']):
    if n % 4 == 0:
        x1,y1=xy(a[i],45,175); x2,y2=xy(b[j],690,175)
        d.line((x1,y1,x2,y2), fill='#b8c7bf', width=2)
for pos, points, color in [(45,a,'#276b57'),(690,b,'#a65e20')]:
    coords=[xy(p,pos,175) for p in points]; d.line(coords, fill=color, width=5)
    for x,y in coords: d.ellipse((x-4,y-4,x+4,y+4), fill=color)
d.text((40, 645), f"32 resampled points per stroke  |  band ratio 0.25  |  DTW distance {item['normalizedDistance']:.3f}", font=regular, fill='#172c27')
d.text((40, 700), 'Gray lines show every fourth pair in the actual computed alignment path.', font=small, fill='#344b45')
d.text((40, 745), 'This example is one stroke, not a claim that the whole character is correct.', font=small, fill='#344b45')
im.save(out / 'actual-dtw.png')
print(json.dumps({'mask_iou': metrics['maskIou'], 'stroke': idx+1, 'dtw_distance': item['normalizedDistance']}))
