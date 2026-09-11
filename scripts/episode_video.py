#!/usr/bin/env python3
"""Paragraph narration, independently aligned captions and multiple shot layouts.

prepare produces audio only; align runs local speech recognition; render is offline.
"""
from __future__ import annotations
import argparse
from concurrent.futures import ThreadPoolExecutor, as_completed
from difflib import SequenceMatcher
import hashlib
import json
import math
import os
from pathlib import Path
import re
import wave

from mimo_tts import DEFAULT_BASE_URL, DEFAULT_MODEL, DEFAULT_STYLE, make_payload, read_key, synthesize
from narrated_video import font_index, font_path, read_audio, run, timestamp

FPS=30

def save(path, data):
    path.parent.mkdir(parents=True,exist_ok=True)
    temporary=path.with_suffix(path.suffix+'.partial')
    temporary.write_text(json.dumps(data,ensure_ascii=False,indent=2)+'\n')
    temporary.replace(path)

def load(path):return json.loads(path.read_text())

def timeline_path(value, directory):
    path=Path(value)
    return path if path.is_absolute() else (directory/path).resolve()

def validate_v2(m, root, images=False):
    if m.get('schema_version')!=2 or not m.get('blocks'):raise ValueError('需要非空 v2 blocks')
    ids=set()
    for b in m['blocks']:
        if not b.get('id') or b['id'] in ids:raise ValueError('段落 id 缺失或重复')
        ids.add(b['id'])
        if not b.get('text','').strip() or re.search(r'\[(画面|停)',b['text']):raise ValueError('需要纯口播')
        if not b.get('shots'):raise ValueError('每段至少一个镜头')
        for s in b['shots']:
            if s.get('layout') not in ('scene','split','table'):raise ValueError('未知画面布局')
            if s['layout']=='table':
                if not 1<=len(s.get('rows',[]))<=6:raise ValueError('数据画面需要 1–6 行')
            elif not s.get('image') or (images and not (root/s['image']).is_file()):
                raise ValueError(f"缺少配图：{s.get('image')}")
    return m

def wav_seconds(path):
    with wave.open(str(path),'rb') as w:return w.getnframes()/w.getframerate()

def fingerprint(m,b):
    cfg=m.get('tts',{})
    payload=make_payload(b['text'],cfg.get('model',DEFAULT_MODEL),cfg.get('voice','白桦'),cfg.get('style',DEFAULT_STYLE))
    return hashlib.sha256(json.dumps({'base':cfg.get('base_url',DEFAULT_BASE_URL),'payload':payload},ensure_ascii=False,sort_keys=True).encode()).hexdigest()[:24]

def prepare(paths, output, offline=False):
    from PIL import ImageFont
    manifests=[(p,validate_v2(load(p),p.parent)) for p in paths]
    for p,m in manifests:ImageFont.truetype(font_path(m),40,index=font_index(m))
    cache=output/'audio-cache';cache.mkdir(parents=True,exist_ok=True)
    jobs={}
    for p,m in manifests:
        for b in m['blocks']:
            target=cache/(fingerprint(m,b)+'.wav')
            if not target.exists():jobs[target]=(m,b)
    if jobs and offline:raise ValueError(f'缺少 {len(jobs)} 段缓存；离线模式未调用接口')
    key=read_key() if jobs else None
    def job(item):
        target,(m,b)=item;cfg=m.get('tts',{})
        seconds=synthesize(b['text'],target,key,cfg.get('base_url',DEFAULT_BASE_URL),cfg.get('model',DEFAULT_MODEL),cfg.get('voice','白桦'),cfg.get('style',DEFAULT_STYLE))
        print(f"配音 {b['id']} · {seconds:.1f}s",flush=True)
    with ThreadPoolExecutor(max_workers=2) as pool:
        futures=[pool.submit(job,j) for j in jobs.items()]
        for f in as_completed(futures):f.result()
    for p,m in manifests:
        edition=output/m['edition'];audio_dir=edition/'audio';audio_dir.mkdir(parents=True,exist_ok=True)
        # Remove only leading/trailing silence, preserving internal phrase pauses.
        for b in m['blocks']:
            if b.get('audio_edit') and b['audio_edit']['cache_fingerprint']!=fingerprint(m,b):
                raise ValueError('音频裁剪与当前语音缓存不匹配；请重新检查剪辑点')
            raw=cache/(fingerprint(m,b)+'.wav');trim=audio_dir/(b['id']+'-trim.wav')
            run(['ffmpeg','-y','-v','error','-i',str(raw),'-af','silenceremove=start_periods=1:start_duration=0.02:start_threshold=-50dB:start_silence=0.06,areverse,silenceremove=start_periods=1:start_duration=0.02:start_threshold=-50dB:start_silence=0.12,areverse','-ar','48000','-ac','1','-c:a','pcm_s16le',str(trim)])
        natural=sum(min(wav_seconds(audio_dir/(b['id']+'-trim.wav')),b.get('audio_edit',{}).get('end_seconds',float('inf'))) for b in m['blocks'])
        tempo=1.0
        if m['edition']=='long' and not 570<=natural<=630:
            tempo=max(.9,min(1.25,natural/600))
        tempo=float(m.get('tempo',tempo))
        if not .8<=tempo<=1.25:raise ValueError('tempo 超出允许的自然语速范围')
        timeline=[];frames_total=0
        with wave.open(str(edition/'narration.wav'),'wb') as whole:
            whole.setparams((1,2,48000,0,'NONE','not compressed'))
            for b in m['blocks']:
                pcm_path=audio_dir/(b['id']+'.wav')
                cut=b.get('audio_edit',{}).get('end_seconds')
                if cut is not None and (cut<=0 or cut>wav_seconds(audio_dir/(b['id']+'-trim.wav'))):raise ValueError('无效音频剪辑点')
                af=f'atrim=end={cut},asetpts=PTS-STARTPTS,' if cut is not None else ''
                run(['ffmpeg','-y','-v','error','-i',str(audio_dir/(b['id']+'-trim.wav')),'-af',af+f'atempo={tempo:.8f}','-ar','48000','-ac','1','-c:a','pcm_s16le',str(pcm_path)])
                pcm=read_audio(pcm_path)
                speech=len(pcm)/96000
                frames=math.ceil((speech+.12)*FPS)
                samples=frames*1600
                pcm+=b'\0'*(samples*2-len(pcm));whole.writeframes(pcm)
                timeline.append({**b,'start_frame':frames_total,'frames':frames,'speech_seconds':speech,'audio':str(pcm_path.relative_to(edition))})
                frames_total+=frames
        save(edition/'audio-timeline.json',{'manifest':os.path.relpath(p.resolve(),edition.resolve()),'natural_seconds':natural,'tempo':tempo,'seconds':frames_total/FPS,'blocks':timeline})
        print(f"{m['edition']} 配音就绪 · {frames_total/FPS:.2f}s · tempo {tempo:.3f}",flush=True)

def int_chinese(n):
    if n==0:return '零'
    digits='零一二三四五六七八九'
    def group(v):
        out='';zero=False
        for divisor,unit in [(1000,'千'),(100,'百'),(10,'十'),(1,'')]:
            d,v=divmod(v,divisor)
            if d:
                if zero:out+='零'
                out+=digits[d]+unit;zero=False
            elif out and v:zero=True
        return out
    if n<10000:s=group(n)
    elif n<100000000:
        a,b=divmod(n,10000);s=group(a)+'万'+('零' if b and b<1000 else '')+(group(b) if b else '')
    else:return ''.join(digits[int(x)] for x in str(n))
    return s[1:] if s.startswith('一十') else s

def normal(text):
    # ASR may write Arabic numbers while narration uses spoken Chinese numbers.
    text=re.sub(r'(?<=\d)[,，](?=\d{3}(?:\D|$))','',text)
    text=re.sub(r'\d+',lambda m:int_chinese(int(m[0])),text)
    return re.sub(r'[^\u4e00-\u9fffA-Za-z]','',text).replace('两','二').replace('〇','零').lower()

def caption_chunks(text,limit=24):
    chunks=[];current=''
    for piece in re.findall(r'[^，。！？；：、]+[，。！？；：、]?',text):
        if len(current)+len(piece)>limit and current:chunks.append(current);current=''
        while len(piece)>limit:
            chunks.append(piece[:limit]);piece=piece[limit:]
        current+=piece
        if current and current[-1] in '。！？；':chunks.append(current);current=''
    if current:chunks.append(current)
    if ''.join(chunks)!=text:raise ValueError('字幕分割丢失正文')
    return chunks

def align_text(text, words, duration):
    observed='';timings=[]
    compact=[]
    for w in words:
        w=dict(w)
        if compact and re.fullmatch(r'[\d,，]+',compact[-1]['word']) and re.fullmatch(r'[\d,，]+[。！？；：]?',w['word']) and w['start']-compact[-1]['end']<.2:
            compact[-1]['word']+=w['word'];compact[-1]['end']=w['end']
        else:compact.append(w)
    for w in compact:
        chars=normal(w['word']);n=len(chars)
        observed+=chars
        for j in range(n):timings.append(w['start']+(w['end']-w['start'])*j/max(1,n))
    expected=normal(text)
    if len(observed)>len(expected)*1.25:raise ValueError('识别到明显超出稿件的内容；请检查重复朗读或额外语音')
    matcher=SequenceMatcher(None,expected,observed,autojunk=False)
    anchors={}
    for match in matcher.get_matching_blocks():
        for d in range(match.size):anchors[match.a+d]=timings[match.b+d]
    ratio=matcher.ratio()
    if not anchors or ratio<.55:raise ValueError(f'语音对齐可信度不足：{ratio:.2f}，需要检查音频/识别结果')
    anchors[-1]=0.;anchors[len(expected)]=duration
    positions=sorted(anchors)
    def at(index):
        if index in anchors:return anchors[index]
        right=next(i for i in positions if i>index);left=max(i for i in positions if i<index)
        return anchors[left]+(anchors[right]-anchors[left])*(index-left)/(right-left)
    chunks=caption_chunks(text);result=[];offset=0
    for chunk in chunks:
        start=max(0.,at(offset));offset+=len(normal(chunk))
        result.append({'start':start,'text':chunk})
    result[0]['start']=0.
    for i,c in enumerate(result):c['end']=result[i+1]['start'] if i+1<len(result) else duration
    return result,ratio,observed

def align(output, editions, model_name='small'):
    from faster_whisper import WhisperModel
    recognizer=WhisperModel(model_name,device='cpu',compute_type='int8',cpu_threads=4,num_workers=1,download_root=str(output/'models'))
    for name in editions:
        directory=output/name;audio=load(directory/'audio-timeline.json');captions=[];audit=[]
        manifest=load(timeline_path(audio['manifest'],directory))
        hint=manifest.get('asr_hint','简体中文。贡献毛利，税前利润，折旧。')
        for b in audio['blocks']:
            cache=directory/'alignment-cache'/(b['id']+'.json')
            audio_file=timeline_path(b['audio'],directory)
            audio_hash=hashlib.sha256(audio_file.read_bytes()).hexdigest()
            stored=load(cache) if cache.exists() else {}
            if stored.get('hash')==audio_hash and stored.get('model')==model_name and stored.get('profile')==3 and stored.get('hint')==hint:
                words=stored['words']
            else:
                segs,_=recognizer.transcribe(str(audio_file),language='zh',beam_size=5,word_timestamps=True,condition_on_previous_text=False,initial_prompt=hint,vad_filter=False)
                words=[{'word':w.word,'start':w.start,'end':w.end} for s in segs for w in (s.words or []) if w.end-w.start>.005]
                save(cache,{'hash':audio_hash,'model':model_name,'profile':3,'hint':hint,'words':words})
            cap,ratio,observed=align_text(b['text'],words,b['speech_seconds'])
            audit.append({'id':b['id'],'match_ratio':round(ratio,4),'recognized':observed,'canonical':normal(b['text'])})
            for c in cap:
                # Frame-quantized boundaries; next caption begins at the previous end.
                captions.append({'block_id':b['id'],'start_frame':b['start_frame']+round(c['start']*FPS),'end_frame':b['start_frame']+round(c['end']*FPS),'text':c['text']})
            print(f"字幕 {name}/{b['id']} · 匹配 {ratio:.1%}",flush=True)
        save(directory/'captions.json',captions);save(directory/'alignment-audit.json',audit)
        (directory/'subtitles.srt').write_text('\n'.join(f"{i+1}\n{timestamp(c['start_frame']/FPS)} --> {timestamp(c['end_frame']/FPS)}\n{c['text']}\n" for i,c in enumerate(captions)))

def typography(m,b,shot,caption,path,progress):
    # Draw editable text/data only. Generated artwork is composited by FFmpeg.
    from PIL import Image,ImageDraw,ImageFont
    layer=Image.new('RGBA',(1920,1080),(0,0,0,0));d=ImageDraw.Draw(layer);font=font_path(m);face=font_index(m)
    ink='#222723';gray='#707A72';orange='#CA6A2D';red='#B44438'
    def text(x,y,s,size=40,color=ink,anchor=None,maxwidth=None):
        size=int(size)
        while maxwidth and d.textlength(str(s),font=ImageFont.truetype(font,size,index=face))>maxwidth and size>18:size-=1
        d.text((x,y),str(s),font=ImageFont.truetype(font,size,index=face),fill=color,anchor=anchor)
    text(82,40,m.get('series_label','拥有一门生意'),23,gray,maxwidth=1100)
    text(1838,40,m.get('disclosure','情景测算'),23,gray,'ra')
    text(80,96,shot['heading'],55,maxwidth=1740)
    d.line((82,181,1838,181),fill='#DADED8',width=2)
    text(82,207,b.get('chapter',''),23,orange)
    if shot['layout']=='split':
        d.line((1080,330,1080,724),fill='#E2E5E0',width=2)
        text(1140,364,shot.get('metric',''),86,red if shot.get('metric','').startswith('−') else orange,maxwidth=675)
        detail=shot.get('detail','');pieces=[detail[i:i+19] for i in range(0,len(detail),19)]
        for i,line in enumerate(pieces):text(1140,492+48*i,line,31)
    elif shot['layout']=='table':
        rows=shot['rows'];step=min(88,480/max(1,len(rows)-1));start=293
        for i,row in enumerate(rows):
            y=start+i*step
            color=orange if i==len(rows)-1 else ink
            if str(row['value']).startswith(('−','-')):color=red
            if row['label'] in caption:
                d.rectangle((140,y+5,145,y+50),fill=orange)
            text(165,y,row['label'],39,color,maxwidth=1000)
            text(1755,y,row['value'],47,color,'ra',maxwidth=660)
            if i<len(rows)-1:d.line((165,y+62,1755,y+62),fill='#E8EBE5',width=1)
    note=shot.get('note','经营金额为演示假设；非真实门店财报、非全国均值')
    if shot.get('source'):note=shot['source']+'；适用范围见随片资料'
    d.rectangle((0,852,1920,918),fill='white')
    text(82,864,note,23,gray,maxwidth=1750)
    d.rectangle((0,918,1920,1080),fill='white')
    lines=[];line=''
    for ch in caption:
        if d.textlength(line+ch,font=ImageFont.truetype(font,46,index=face))>1720:lines.append(line);line=''
        line+=ch
    if line:lines.append(line)
    if len(lines)>2:raise ValueError('字幕超出安全区')
    for i,line in enumerate(lines):text(960,957+i*57,line,46,anchor='ma')
    d.rectangle((82,1056,1838,1060),fill='#EAEEE7')
    d.rectangle((82,1056,82+round(1756*progress),1060),fill=orange)
    layer.save(path)

def shot_timeline(blocks):
    result=[]
    for b in blocks:
        # Explicit cuts can be tied to narration phrases; default at caption boundaries.
        count=len(b['shots'])
        for i,s in enumerate(b['shots']):
            start=b['start_frame']+round(b['frames']*i/count)
            end=b['start_frame']+round(b['frames']*(i+1)/count)
            result.append({**s,'id':f"{b['id']}-{i+1}",'block_id':b['id'],'start_frame':start,'end_frame':end})
    return result

def render(output, edition, workers=3):
    directory=output/edition;audio=load(directory/'audio-timeline.json');manifest=timeline_path(audio['manifest'],directory);root=manifest.parent
    m=validate_v2(load(manifest),root,images=True);captions=load(directory/'captions.json')
    # Use current visual authoring while keeping verified audio text invariant.
    for old,new in zip(audio['blocks'],m['blocks']):
        if old['text']!=new['text'] or old['id']!=new['id']:raise ValueError('正文变更后需重新 prepare + align')
        old['shots']=new['shots'];old['chapter']=new['chapter']
    if len(audio['blocks'])!=len(m['blocks']):raise ValueError('段落数量已改变')
    shots=shot_timeline(audio['blocks']);total=sum(b['frames'] for b in audio['blocks'])
    # Align visual midpoint cuts to the closest subtitle boundary within that paragraph.
    for i,s in enumerate(shots):
        if i and shots[i-1]['block_id']==s['block_id']:
            candidates=[c['start_frame'] for c in captions if c['block_id']==s['block_id'] and c['start_frame']>shots[i-1]['start_frame']+FPS and c['start_frame']<s['end_frame']-FPS]
            if candidates:
                cut=min(candidates,key=lambda t:abs(t-s['start_frame']));shots[i-1]['end_frame']=cut;s['start_frame']=cut
    boundaries=sorted({0,total,*[s['start_frame'] for s in shots],*[s['end_frame'] for s in shots],*[c['start_frame'] for c in captions],*[c['end_frame'] for c in captions]})
    parts=[]
    for start,end in zip(boundaries,boundaries[1:]):
        if end<=start:continue
        shot=next(s for s in shots if s['start_frame']<=start<s['end_frame'])
        b=next(b for b in audio['blocks'] if b['id']==shot['block_id'])
        caption=next((c['text'] for c in captions if c['start_frame']<=start<c['end_frame']),'')
        parts.append((start,end,shot,b,caption))
    render_dir=directory/'render';render_dir.mkdir(exist_ok=True)
    def part_job(index,part):
        start,end,s,b,caption=part;frames=end-start
        overlay=render_dir/f'{index:04d}-text.png';clip=render_dir/f'{index:04d}.mp4';stamp=render_dir/f'{index:04d}.sha'
        spec={'part':part,'series_label':m.get('series_label'),'disclosure':m.get('disclosure'),'font':font_path(m),'font_index':font_index(m),'renderer':9}
        if s.get('image'):spec['image_hash']=hashlib.sha256((root/s['image']).read_bytes()).hexdigest()
        digest=hashlib.sha256(json.dumps(spec,ensure_ascii=False,sort_keys=True).encode()).hexdigest()
        if clip.exists() and stamp.exists() and stamp.read_text()==digest:return clip
        typography(m,b,s,caption,overlay,end/total)
        cmd=['ffmpeg','-y','-v','error']
        if s['layout']=='table':cmd+=['-f','lavfi','-i','color=c=white:s=1920x1080:r=30']
        else:cmd+=['-loop','1','-framerate','30','-i',str(root/s['image'])]
        cmd+=['-loop','1','-framerate','30','-i',str(overlay)]
        if s['layout']=='table':base='[0:v]setsar=1[bg];'
        else:
            if s['layout']=='split':w,h,x,y=1040,584,28,270
            else:w,h,x,y=1280,720,320,230
            # Hold artwork still within a shot; only explicit shot cuts change it.
            base=f"[0:v]scale={w}:{h}:flags=lanczos,pad=1920:1080:{x}:{y}:color=white,setsar=1[bg];"
        cmd+=['-filter_complex',base+'[bg][1:v]overlay=0:0,format=yuv420p[v]','-map','[v]','-frames:v',str(frames),'-an','-c:v','libx264','-preset','veryfast','-crf','19','-threads','2',str(clip)]
        run(cmd);stamp.write_text(digest);return clip
    files=[None]*len(parts)
    with ThreadPoolExecutor(max_workers=workers) as pool:
        futures={pool.submit(part_job,i,p):i for i,p in enumerate(parts)}
        for f in as_completed(futures):
            i=futures[f];files[i]=f.result()
            if (i+1)%20==0:print(f'渲染 {edition} · {i+1}/{len(parts)}',flush=True)
    concat=render_dir/'concat.txt';concat.write_text(''.join(f"file '{p.name}'\n" for p in files))
    picture=directory/'picture.mp4'
    run(['ffmpeg','-y','-v','error','-f','concat','-safe','1','-i',str(concat),'-c','copy',str(picture)])
    # Two-pass loudness normalization keeps the narration level predictable.
    import subprocess
    measure=subprocess.run(['ffmpeg','-hide_banner','-i',str(directory/'narration.wav'),'-af','loudnorm=I=-16:TP=-1.5:LRA=11:print_format=json','-f','null','-'],capture_output=True,text=True)
    if measure.returncode:raise RuntimeError(measure.stderr[-1000:])
    loud=json.JSONDecoder().raw_decode(measure.stderr[measure.stderr.rfind('{'):])[0]
    params=':'.join(f'{a}={loud[b]}' for a,b in [('measured_I','input_i'),('measured_TP','input_tp'),('measured_LRA','input_lra'),('measured_thresh','input_thresh'),('offset','target_offset')])
    final=directory/'video.mp4'
    run(['ffmpeg','-y','-v','error','-i',str(picture),'-i',str(directory/'narration.wav'),'-map','0:v:0','-map','1:a:0','-c:v','copy','-af','loudnorm=I=-16:TP=-1.5:LRA=11:linear=true:'+params,'-ar','48000','-c:a','aac','-b:a','192k','-t',str(total/FPS),'-movflags','+faststart',str(final)])
    save(directory/'timeline.json',{'fps':FPS,'seconds':total/FPS,'shots':shots,'captions':captions,'render_parts':len(parts)})
    save(directory/'media-info.json',json.loads(run(['ffprobe','-v','error','-show_streams','-show_format','-of','json',str(final)])))
    save(directory/'loudness.json',loud)
    print(f'完成 {final} · {total/FPS:.2f}s · {len(shots)} 镜头',flush=True)

def main():
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('stage',choices=['prepare','align','render']);parser.add_argument('manifests',nargs='*',type=Path)
    parser.add_argument('--output',type=Path,default=Path('outputs/laundromat-v2'));parser.add_argument('--editions',nargs='+',default=['short','long']);parser.add_argument('--offline',action='store_true');parser.add_argument('--model',default='small');parser.add_argument('--workers',type=int,default=3)
    a=parser.parse_args();out=a.output.resolve();out.mkdir(parents=True,exist_ok=True)
    if a.stage=='prepare':
        if not a.manifests:parser.error('prepare 需要清单路径')
        prepare([p.resolve() for p in a.manifests],out,a.offline)
    elif a.stage=='align':align(out,a.editions,a.model)
    else:
        for edition in a.editions:render(out,edition,a.workers)

if __name__=='__main__':main()
