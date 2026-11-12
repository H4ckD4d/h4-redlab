"""Defensive event triage from synthetic JSONL. No network access or attack execution."""
import json
from pathlib import Path

def analyze(path):
    events=[]
    with open(path,encoding='utf-8') as f:
        for line in f:
            if line.strip():
                events.append(json.loads(line))
    counts={}; alerts=[]
    for e in events:
        if e.get('event')=='login_failed':
            key=e.get('actor','unknown'); counts[key]=counts.get(key,0)+1
        elif e.get('event')=='privilege_granted':
            alerts.append({'rule':'review-privilege-change','actor':e.get('actor','unknown'),'severity':'review'})
    for actor,count in counts.items():
        if count>=3:
            alerts.append({'rule':'repeated-login-failure','actor':actor,'count':count,'severity':'review'})
    return {'events':len(events),'alerts':alerts,'note':'Offline, fictional events. Human review required.'}

def configure(sub):
    p=sub.add_parser('analyze',help='Analyze fictional JSONL event data')
    p.add_argument('path')

def run(args):
    return analyze(args.path)

def demo():
    return analyze(Path(__file__).resolve().parents[2]/'samples'/'events.jsonl')
