"""Rebuild the style-consistency revision with the unchanged 23-shot timing and narration."""
import hashlib
import json
import os
from pathlib import Path
import shutil

from PIL import Image, ImageDraw

HERE=Path(__file__).resolve().parent
REPO=HERE.parents[2]
BASE=REPO/'examples/video/laundromat-v2'
OLD=REPO/'outputs/laundromat-v2/short'
OUT=REPO/'outputs/laundromat-dense-pilot-v2-clean/short'
INK='#263830';GREEN='#2F7166';ORANGE='#CF7135';RED='#B44B43';PAPER='#FAF4E8'

def write(p,data):
    p.parent.mkdir(parents=True,exist_ok=True)
    p.write_text(json.dumps(data,ensure_ascii=False,indent=2)+'\n')

def graphic(name,draw):
    image=Image.new('RGB',(1920,1080),PAPER)
    draw(ImageDraw.Draw(image))
    image.save(HERE/'images'/f'{name}.png')

def machine(d,x,y,accent=GREEN):
    d.rounded_rectangle((x,y,x+115,y+140),14,fill='white',outline=INK,width=4)
    d.line((x+8,y+30,x+107,y+30),fill=INK,width=3)
    d.ellipse((x+23,y+48,x+93,y+118),fill=accent,outline=INK,width=4)
    d.ellipse((x+87,y+11,x+97,y+21),fill=ORANGE)

def charts():
    def attach(d):
        for i in range(10):machine(d,170+i%5*135,355+i//5*185)
        for i in range(6):machine(d,1190+i%3*155,355+i//3*185,ORANGE)
        d.line((915,520,1100,520),fill=INK,width=8)
        d.polygon([(1100,520),(1065,500),(1065,540)],fill=INK)
    graphic('attach',attach)
    def contribution(d):
        x,y,w,h=220,460,1480,190
        d.rounded_rectangle((x,y,x+w,y+h),18,fill=GREEN)
        d.rectangle((x,y,x+round(w*4.8/18),y+h),fill=RED)
    graphic('contribution',contribution)
    def calendar(d):
        d.rounded_rectangle((585,215,1335,825),30,fill='white',outline=INK,width=6)
        d.rounded_rectangle((585,215,1335,340),30,fill=ORANGE)
        d.rectangle((585,275,1335,340),fill=ORANGE)
        for x in (730,1190):d.line((x,165,x,265),fill=INK,width=18)
        for row in range(4):
            for col in range(7):
                x=650+col*90;y=410+row*85
                d.rounded_rectangle((x,y,x+43,y+36),6,fill='#DCE6DE')
    graphic('calendar',calendar)
    def income(d):
        # A native proportion diagram, not currency art or a claim about coin counts.
        for i in range(18):
            x=325+i%9*145;y=360+i//9*190
            d.rounded_rectangle((x,y,x+105,y+130),12,fill='#E4AE63',outline=INK,width=4)
    graphic('income',income)
    def year(d):
        d.line((340,635,1580,635),fill='#D5DFD7',width=7)
        for x in (420,960,1500):d.ellipse((x-20,615,x+20,655),fill=ORANGE)
    graphic('year',year)
    def loss(d):
        zero=970;scale=700/57600
        d.line((zero,265,zero,740),fill=INK,width=4)
        d.rounded_rectangle((zero,330,zero+round(57600*scale),445),12,fill=GREEN)
        d.rounded_rectangle((zero-round(37440*scale),545,zero,660),12,fill=RED)
    graphic('loss',loss)
    def threshold(d):
        left,right,y=270,1650,570
        x=left+(38-20)/(60-20)*(right-left)
        d.line((left,y,x,y),fill=RED,width=20);d.line((x,y,right,y),fill=GREEN,width=20)
        for n in (20,30,38,50,60):
            p=left+(n-20)/40*(right-left)
            d.line((p,y-20,p,y+20),fill=INK,width=4)
        d.ellipse((x-22,y-22,x+22,y+22),fill=ORANGE,outline=INK,width=4)
    graphic('threshold',threshold)

def label(text,x=.23,y=.43,size=100,color=INK,**kw):
    return dict(text=text,x=x,y=y,size=size,color=color,**kw)

def left(big,small,*,color=ORANGE,background=None):
    return [label(big,x=.22,size=94,color=color,background=background),label(small,x=.22,y=.58,size=38,color=color)]

def shot(image,at,idea,labels=(),character=False):
    return dict(layout='full',image=f'images/{image}.png',at_seconds=at,heading=idea,
                labels=list(labels),character_present=character,core_idea=idea)

def main():
    (HERE/'images').mkdir(exist_ok=True);OUT.mkdir(parents=True,exist_ok=True)
    charts()
    m=json.loads((BASE/'short.json').read_text())
    m.update(profile='dense-illustrated-static-v1',revision='style-consistency-v2-clean',disclosure='',status='visual-trial-awaiting-feedback')
    plans=[
        [shot('storefront',0,'进入社区洗烘店'),
         shot('intake',4,'从一筒衣服开始算账',[label('一年能剩多少？',.25,.39,72),label('跟着一筒衣服算',.25,.53,42,color=GREEN)])],
        [shot('washer',0,'洗衣成交价',left('12 元','洗一次')),
         shot('dryer',1.74,'烘干成交价',left('10 元','烘一次')),
         shot('attach',4.12,'洗衣与烘干组合',[label('10 次洗衣',.265,.22,70),label('6 次烘干',.755,.22,70),label('平均烘干比例 60%',.5,.77,48,color=GREEN)])],
        [shot('income',0,'组合收入',[label('18 元',.5,.22,120),label('每次洗衣及平均带来的烘干',.5,.73,46,color=GREEN)]),
         shot('costs',3.98,'扣变动成本',left('−4.8 元','能源 · 耗材 · 交易费用',color=RED)),
         shot('contribution',6.2,'剩下的是贡献毛利',[label('18 − 4.8 = 13.2 元',.5,.26,100),label('变动成本',.215,.69,40,color=RED),label('贡献毛利，尚需承担固定开支',.62,.69,40,color=GREEN)])],
        [shot('busy',0,'每日订单假设',[label('50 筒 / 日',.5,.19,92,background='#FEFDF9')],True),
         shot('calendar',1.94,'全年营业天数',[label('360 天',.5,.46,120),label('每年营业',.5,.72,44,color=GREEN)]),
         shot('year',4.52,'全年贡献',[label('237,600 元',.5,.25,130),label('年度贡献毛利',.5,.40,52,color=GREEN),label('13.2 元 / 筒',.22,.52,52),label('50 筒 / 日',.5,.52,52),label('360 天',.78,.52,52)])],
        [shot('rent',0,'租金仍然发生',left('−72,000 元','年度房租',color=RED,background='#FEFDF9')),
         shot('cleaning',2.38,'店主劳动有成本',[label('−48,000 元',.20,.30,94,color=RED),label('人工 · 已计店主劳动',.20,.43,38,color=RED)],True)],
        [shot('tools',0,'其他运营成本',left('−18,000 元','年度其他运营',color=RED)),
         shot('wear',2.1,'折旧是年度损耗',[label('−42,000',.235,.30,86,color=RED),label('元 / 年 · 折旧',.235,.42,38)]),
         shot('ledger',3.66,'全年税前利润',left('57,600 元','年度税前利润',color=GREEN))],
        [shot('empty',0,'订单下滑到三十筒',[label('30 筒 / 日',.205,.32,92),label('同一家店，客流变少',.205,.45,38)]),
         shot('loss',2.1,'同条件下盈亏反差',[label('50 筒 / 日',.16,.35,48),label('+57,600 元',.73,.36,72,color='white'),label('30 筒 / 日',.16,.55,48),label('−37,440 元',.74,.55,82,color=RED),label('年度税前结果 · 其他条件不变',.5,.78,40)])],
        [shot('threshold',0,'找出盈亏平衡位置',[label('先找到打平的门槛',.5,.24,78),label('亏损',.24,.68,42,color=RED),label('盈利',.76,.68,42,color=GREEN)]),
         shot('threshold',2.5,'每天约三十八筒',[label('约 38 筒 / 日',.5,.26,110,color=ORANGE),label('价格与烘干比例保持不变',.5,.40,40),label('20',.14,.66,36),label('30',.32,.66,36),label('38',.464,.66,44,color=ORANGE),label('50',.68,.66,36),label('60',.86,.66,36)])],
        [shot('intake',0,'强调假设边界',[label('这是一组假设',.25,.37,74),label('不是行业均值',.25,.53,48,color=RED)]),
         shot('storefront',2.82,'回到真实门店'),
         shot('ledger',6.0,'真实条件决定结果',[label('最后剩多少',.24,.37,88),label('由真实门店条件决定',.24,.53,42,color=GREEN)])],
    ]
    for b,shots in zip(m['blocks'],plans):
        b['shots']=shots;b.pop('audio_edit',None)
    write(HERE/'short.json',m)
    for filename in ('ledger.json','sources.md'):
        shutil.copy2(BASE/filename,HERE/filename)
    original=json.loads((OLD/'audio-timeline.json').read_text())
    expected=next(x['sha256'] for x in json.loads((BASE/'approved-baseline.json').read_text())['outputs'] if x['path']=='outputs/laundromat-v2/short/narration.wav')
    actual=hashlib.sha256((OLD/'narration.wav').read_bytes()).hexdigest()
    if actual!=expected:raise ValueError('参考配音与确认版指纹不一致')
    for name in ('narration.wav','captions.json','subtitles.srt'):
        shutil.copy2(OLD/name,OUT/name)
    (OUT/'audio').mkdir(exist_ok=True)
    for old,new in zip(original['blocks'],m['blocks']):
        if old['text']!=new['text'] or old['id']!=new['id']:raise ValueError('本次只允许视觉改版')
        src=Path(old['audio']) if Path(old['audio']).is_absolute() else OLD/old['audio']
        shutil.copy2(src,OUT/'audio'/src.name)
        old.update(new);old['audio']=f'audio/{src.name}';old.pop('audio_edit',None)
    original['manifest']=os.path.relpath(HERE/'short.json',OUT)
    write(OUT/'audio-timeline.json',original)
    write(HERE/'audio-reuse.json',{'source':'../laundromat-v2/short.json','source_narration':'outputs/laundromat-v2/short/narration.wav','sha256':actual,'changes':'visuals only; same narration, captions, ledger and block timings','cut_source':'at_seconds measured from the exact S01–S09 alignment-cache word timestamps; S08 2.5s reveals the threshold at 约; repeated threshold is a labeled state change'})
    lines=['# 洗烘店密集插画试片 · 画风统一修订','', '同一配音、同一账本、同一 23 镜切点；统一画风，将突出人物的算账画面改为物件。人物只在使用机器、清洁的场景中出现。','', '| 段落 / 段内起点 | 核心意思 | 画面 | 人物 |','|---|---|---|---|']
    for b in m['blocks']:
        for s in b['shots']:lines.append(f"| {b['id']} / {s['at_seconds']:.2f}s | {s['core_idea']} | {s['image']} | {'有' if s['character_present'] else '无'} |")
    (HERE/'storyboard.md').write_text('\n'.join(lines)+'\n')
    (HERE/'script.md').write_text('# 试片原稿\n\n'+'\n\n'.join(b['text'] for b in m['blocks'])+'\n')
    print('Prepared',sum(len(b['shots']) for b in m['blocks']),'shots; exact approved narration reused.')

if __name__=='__main__':main()
