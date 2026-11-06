"""Chấm offline theo bao_asr_v1; chỉ dùng Python standard library, không tải model."""
import argparse
import csv
import hashlib
import json
import unicodedata as ud
from pathlib import Path

NORMALIZER_ID = 'vi_nfc_ps_space_v1'
TONES = {'\u0300','\u0301','\u0303','\u0309','\u0323'}

def normalize(s):
    s = ud.normalize('NFC', s).lower()
    s = ''.join(' ' if ud.category(c)[0] in 'PS' else c for c in s)
    return ' '.join(s.split())

def without_tone(s):
    # Chỉ bỏ dấu thanh, giữ ă â ê ô ơ ư và đ.
    return ud.normalize('NFC',''.join(c for c in ud.normalize('NFD',s) if c not in TONES))

def align(ref, hyp):
    n,m=len(ref),len(hyp)
    dp=[[0]*(m+1) for _ in range(n+1)]
    for i in range(n+1): dp[i][0]=i
    for j in range(m+1): dp[0][j]=j
    for i in range(1,n+1):
        for j in range(1,m+1):
            dp[i][j]=min(dp[i-1][j-1]+(ref[i-1]!=hyp[j-1]),dp[i-1][j]+1,dp[i][j-1]+1)
    ops=[]; i,j=n,m
    while i or j:
        if i and j and ref[i-1]==hyp[j-1] and dp[i][j]==dp[i-1][j-1]:
            ops.append({'op':'H','ref':ref[i-1],'hyp':hyp[j-1],'ri':i-1,'hi':j-1});i-=1;j-=1
        elif i and j and dp[i][j]==dp[i-1][j-1]+1:
            ops.append({'op':'S','ref':ref[i-1],'hyp':hyp[j-1],'ri':i-1,'hi':j-1});i-=1;j-=1
        elif i and dp[i][j]==dp[i-1][j]+1:
            ops.append({'op':'D','ref':ref[i-1],'hyp':'','ri':i-1,'hi':None});i-=1
        else:
            ops.append({'op':'I','ref':'','hyp':hyp[j-1],'ri':None,'hi':j-1});j-=1
    ops.reverse()
    counts={k:sum(o['op']==k for o in ops) for k in 'SDIH'}
    counts['N']=n
    assert counts['H']+counts['S']+counts['D']==n
    assert counts['S']+counts['D']+counts['I']==dp[n][m]
    return counts,ops

def score(ref,hyp):
    r,h=normalize(ref),normalize(hyp)
    if not r:
        raise ValueError('Nhãn tham chiếu rỗng sau chuẩn hóa; audit dữ liệu trước khi chấm')
    w,wo=align(r.split(),h.split())
    c,co=align(list(r.replace(' ','')),list(h.replace(' ','')))
    return {'reference_norm':r,'hypothesis_norm':h,'word_counts':w,'char_counts':c,
            'WER_percent':100*(w['S']+w['D']+w['I'])/w['N'],
            'CER_percent':100*(c['S']+c['D']+c['I'])/c['N'],
            'word_alignment':wo,'char_alignment':co,
            'tone_only_substitutions':sum(o['op']=='S' and o['ref']!=o['hyp'] and without_tone(o['ref'])==without_tone(o['hyp']) for o in wo)}

def load(path):
    records=[]
    with Path(path).open(encoding='utf-8-sig') as f:
        for line_no,line in enumerate(f,1):
            if not line.strip(): continue
            r=json.loads(line)
            if not isinstance(r.get('id'),str) or not r['id']:
                raise ValueError(f'{path}:{line_no}: thiếu id dạng chuỗi')
            records.append(r)
    ids=[r['id'] for r in records]
    if len(ids)!=len(set(ids)): raise ValueError(f'{path}: trùng id bản thu')
    if not ids: raise ValueError(f'{path}: file rỗng')
    return records

def sha(path): return hashlib.sha256(Path(path).read_bytes()).hexdigest()

def main():
    ap=argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--predictions',required=True,help='JSONL: id, reference, prediction (raw text)')
    ap.add_argument('--manifest',required=True,help='JSONL độc lập: id, reference; đúng toàn bộ split')
    ap.add_argument('--out',required=True,help='Thư mục MỚI; chặn ghi đè')
    ap.add_argument('--run-id',required=True)
    args=ap.parse_args()
    preds=load(args.predictions); manifest=load(args.manifest)
    expected={r['id']:r for r in manifest}; actual={r['id']:r for r in preds}
    if expected.keys()!=actual.keys():
        raise ValueError(f'IDs không khớp: thiếu {sorted(expected.keys()-actual.keys())[:10]}, thừa {sorted(actual.keys()-expected.keys())[:10]}')
    fingerprints={r.get('run_fingerprint') for r in preds if r.get('run_fingerprint')}
    if len(fingerprints)>1: raise ValueError('Trộn nhiều run_fingerprint trong file dự đoán')
    output=[]
    for key in sorted(expected):
        r=actual[key]; e=expected[key]
        if not all(isinstance(r.get(k),str) for k in ['reference','prediction']) or not isinstance(e.get('reference'),str):
            raise ValueError(f'{key}: reference/prediction phải là raw string; prediction rỗng được chấp nhận')
        if r['reference']!=e['reference']: raise ValueError(f'{key}: reference raw khác manifest')
        output.append({'id':key,'run_id':args.run_id,'reference_raw':r['reference'],'hypothesis_raw':r['prediction'],
                       'speaker_id':r.get('speaker_id'),'sent_id':r.get('sent_id'),**score(r['reference'],r['prediction'])})
    total={}
    for kind in ['word_counts','char_counts']:
        total[kind]={k:sum(r[kind][k] for r in output) for k in 'SDIHN'}
    w,c=total['word_counts'],total['char_counts']
    summary={'run_id':args.run_id,'n':len(output),'status':'SCORED_PREDICTIONS_ONLY','normalizer_id':NORMALIZER_ID,
             'alignment_tie_order':'H S D I','WER_percent':100*(w['S']+w['D']+w['I'])/w['N'],
             'CER_percent':100*(c['S']+c['D']+c['I'])/c['N'],**total,
             'predictions_sha256':sha(args.predictions),'manifest_sha256':sha(args.manifest),
             'scorer_sha256':sha(__file__),'run_fingerprints':sorted(fingerprints),
             'note':'Không chứng nhận chất lượng audio, checkpoint hoặc timing; cần run metadata riêng.'}
    dest=Path(args.out); dest.mkdir(parents=True,exist_ok=False)
    (dest/'summary.json').write_text(json.dumps(summary,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    (dest/'alignments.jsonl').write_text(''.join(json.dumps(r,ensure_ascii=False)+'\n' for r in output),encoding='utf-8')
    with (dest/'per_utterance.csv').open('w',encoding='utf-8-sig',newline='') as f:
        fields=['id','run_id','speaker_id','sent_id','reference_raw','hypothesis_raw','reference_norm','hypothesis_norm','S','D','I','N','Sc','Dc','Ic','Nc','WER_percent','CER_percent','tone_only_substitutions']
        writer=csv.DictWriter(f,fieldnames=fields); writer.writeheader()
        for row in output:
            flat={k:row[k] for k in fields if k in row}
            flat.update({k:row['word_counts'][k] for k in 'SDIN'})
            flat.update({k+'c':row['char_counts'][k] for k in 'SDIN'})
            writer.writerow(flat)
    print(json.dumps(summary,ensure_ascii=False,indent=2))

if __name__=='__main__': main()
