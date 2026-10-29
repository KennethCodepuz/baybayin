from PIL import Image, ImageDraw, ImageFont
from pathlib import Path

out = Path('tmp/chapter3-figures')
out.mkdir(parents=True, exist_ok=True)
font = ImageFont.truetype('C:/Windows/Fonts/arial.ttf', 23)
small = ImageFont.truetype('C:/Windows/Fonts/arial.ttf', 19)
bold = ImageFont.truetype('C:/Windows/Fonts/arialbd.ttf', 25)

def canvas(title, height=430):
    im = Image.new('RGB', (1400, height), 'white')
    d = ImageDraw.Draw(im)
    d.text((35, 20), title, font=bold, fill='#183b35')
    return im, d

def box(d, bounds, text, fill='#e8f1ed'):
    d.rounded_rectangle(bounds, radius=12, fill=fill, outline='#477669', width=3)
    x0,y0,x1,y1 = bounds
    d.multiline_text(((x0+x1)/2, (y0+y1)/2), text, font=font, fill='#172c27', anchor='mm', align='center', spacing=7)

def arrow(d, start, end):
    d.line((start,end), fill='#477669', width=4)
    x,y=end
    d.polygon([(x,y),(x-13,y-8),(x-13,y+8)], fill='#477669')

im,d=canvas('Research pipeline: from recordings to model use', 390)
labels=['Expert references\n+ group attempts','Clean and label\nExcel manifest','Extract image\n+ stroke features','Writer-separated\nmodel evaluation','Train all-data model\n+ test in app']
for i,label in enumerate(labels):
    x=25+i*278
    box(d,(x,110,x+235,235),label)
    if i<4: arrow(d,(x+235,173),(x+272,173))
d.text((40,290),'Expert references are used for comparison; the three group writers supply training/test attempts.',font=small,fill='#344b45')
im.save(out/'pipeline.png')

im,d=canvas('Controlled data collection', 390)
box(d,(40,95,330,220),'Expert writer\n12 reference symbols')
box(d,(410,95,720,220),'3 group writers\nW01, W02, W03')
box(d,(800,95,1350,220),'12 targets per writer\n6 plain × 4 + 6 modified × 5\n= 54 attempts per writer')
arrow(d,(330,155),(400,155));arrow(d,(720,155),(790,155))
d.text((55,275),'Total: 162 group attempts  |  36 intended-conforming  |  126 controlled errors',font=font,fill='#172c27')
d.text((55,320),'Labels describe the intended error and await individual expert review.',font=small,fill='#344b45')
im.save(out/'collection.png')

im,d=canvas('Two complementary feature paths', 500)
box(d,(30,135,250,270),'Expert + learner\nrecordings')
box(d,(360,75,620,185),'Final PNG\nnormalize + mask')
box(d,(730,75,1000,185),'Intersection / union\ncentroid difference')
box(d,(360,270,620,380),'Ordered events\nsegment + resample')
box(d,(730,270,1000,380),'Constrained DTW\n+ count + direction')
box(d,(1110,165,1370,295),'9 numerical\nfeatures')
arrow(d,(250,165),(350,130));arrow(d,(620,130),(720,130));arrow(d,(1000,130),(1100,205))
arrow(d,(250,240),(350,325));arrow(d,(620,325),(720,325));arrow(d,(1000,325),(1100,250))
im.save(out/'modalities.png')

im,d=canvas('Mask overlap and DTW: illustrative example', 530)
d.text((55,75),'Image form: normalize ink → binary masks → overlap',font=font,fill='#172c27')
for x,label in [(70,'Expert mask'),(300,'Learner mask'),(530,'Overlap / union')]:
    d.rectangle((x,120,x+150,270),outline='#52685f',width=2)
    d.line((x+35,235,x+115,155),fill='#213e36',width=16)
    if label!='Expert mask': d.line((x+45,240,x+125,170),fill='#8fbdac',width=9)
    d.text((x,285),label,font=small,fill='#172c27')
d.text((760,75),'Ordered stroke comparison',font=font,fill='#172c27')
for x,y,label in [(790,140,'Expert'),(790,275,'Learner')]:
    d.text((x,y-38),label,font=small,fill='#172c27')
    pts=[(x+30,y+80),(x+90,y+45),(x+160,y+70),(x+230,y+5),(x+320,y+25)]
    d.line(pts,fill='#347c6b',width=5)
    for p in pts: d.ellipse((p[0]-6,p[1]-6,p[0]+6,p[1]+6),fill='#347c6b')
for dx in [30,90,160,230,320]: d.line((820+dx,222,820+dx,273),fill='#a4bdb4',width=2)
d.text((55,420),'DTW aligns resampled points in order within a band; it measures path difference, not writing speed.',font=small,fill='#344b45')
im.save(out/'mask-dtw.png')

im,d=canvas('Writer-separated evaluation and deployment training', 430)
for i,(train,test) in enumerate([('W02 + W03','W01'),('W01 + W03','W02'),('W01 + W02','W03')]):
    y=85+i*90
    box(d,(50,y,380,y+65),f'Train: {train}  (108)', '#e8f1ed')
    arrow(d,(380,y+32),(480,y+32))
    box(d,(490,y,800,y+65),f'Test: {test}  (54)', '#f6eee2')
    arrow(d,(800,y+32),(900,y+32))
    box(d,(910,y,1350,y+65),'Held-out predictions', '#eef0f5')
d.text((65,375),'After evaluation: fit a separate deployment model on all 162 attempts.',font=small,fill='#344b45')
im.save(out/'folds.png')
