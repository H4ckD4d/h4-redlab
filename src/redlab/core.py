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
    t=sub.add_parser('timeline',help='Analyze timezone-aware fictional events in a sliding time window')
    t.add_argument('path');t.add_argument('--minutes',type=int,default=10)
    t.add_argument('--threshold',type=int,default=3)

def run(args):
    return analyze_windowed(args.path,args.minutes,args.threshold) if args.command=='timeline' else analyze(args.path)

def demo():
    return analyze(Path(__file__).resolve().parents[2]/'samples'/'events.jsonl')

def analyze_windowed(path, minutes=10, threshold=3):
    """Offline failure-burst detection using timezone-aware synthetic timestamps.

    Sorts events by timestamp. Bursts group by (actor, origin); no network access.
    """
    from collections import defaultdict, deque
    from datetime import datetime, timedelta, timezone
    if not 1 <= minutes <= 1440 or not 2 <= threshold <= 100:
        raise ValueError('Invalid window or threshold')
    parsed=[]
    with open(path, encoding='utf-8') as stream:
        for line_number, line in enumerate(stream, 1):
            if not line.strip():
                continue
            event=json.loads(line)
            timestamp=event.get('timestamp')
            try:
                instant=datetime.fromisoformat(timestamp.replace('Z','+00:00'))
                if instant.tzinfo is None:
                    raise ValueError('Missing timezone')
            except (AttributeError, ValueError, TypeError) as exc:
                raise ValueError(f'Event {line_number} has invalid timezone-aware timestamp') from exc
            parsed.append((instant.astimezone(timezone.utc), event))
    parsed.sort(key=lambda pair: pair[0])
    buckets=defaultdict(deque); alerts=[]
    duration=timedelta(minutes=minutes)
    for instant,event in parsed:
        if event.get('event')=='privilege_granted':
            alerts.append({'rule':'review-privilege-change','actor':event.get('actor','unknown'),
                           'timestamp_utc':instant.isoformat(),'severity':'review'})
        if event.get('event')!='login_failed':
            continue
        actor=event.get('actor','unknown'); origin=event.get('origin','unknown')
        key=(actor,origin); queue=buckets[key]
        while queue and instant-queue[0] > duration:
            queue.popleft()
        queue.append(instant)
        if len(queue)>=threshold:
            alerts.append({'rule':'login-failure-burst','actor':actor,'origin':origin,
                           'count':len(queue),'timestamp_utc':instant.isoformat(),'severity':'review'})
            queue.clear()
    return {'events':len(parsed),'window_minutes':minutes,'threshold':threshold,
            'alerts':alerts,'note':'Offline analysis; requires synthetic or authorized data. Human review required.'}
