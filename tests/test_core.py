import tempfile, unittest, json
from pathlib import Path
from redlab.core import analyze
class CoreTests(unittest.TestCase):
    def test_failure_and_privilege_alerts(self):
        with tempfile.TemporaryDirectory() as d:
            p=Path(d)/'events.jsonl'
            rows=[{'actor':'demo','event':'login_failed'}]*3+[{'actor':'admin-demo','event':'privilege_granted'}]
            p.write_text(''.join(json.dumps(x)+'\n' for x in rows))
            result=analyze(p)
            self.assertEqual(len(result['alerts']),2)
    def test_no_alert_for_one_failure(self):
        with tempfile.TemporaryDirectory() as d:
            p=Path(d)/'events.jsonl';p.write_text(json.dumps({'actor':'demo','event':'login_failed'})+'\n')
            self.assertEqual(analyze(p)['alerts'],[])

    def test_burst_window_separates_distant_events(self):
        from redlab.core import analyze_windowed
        with tempfile.TemporaryDirectory() as d:
            p=Path(d)/'events.jsonl'
            rows=[{'actor':'synthetic','event':'login_failed','origin':'192.0.2.10',
                   'timestamp':f'2026-01-01T00:{m:02d}:00Z'} for m in (0,1,2,40)]
            p.write_text(''.join(json.dumps(x)+'\n' for x in rows))
            result=analyze_windowed(p,minutes=5,threshold=3)
            self.assertEqual(len(result['alerts']),1)
            self.assertEqual(result['alerts'][0]['count'],3)
    def test_window_requires_timezone_aware_timestamp(self):
        from redlab.core import analyze_windowed
        with tempfile.TemporaryDirectory() as d:
            p=Path(d)/'events.jsonl';p.write_text(json.dumps({'timestamp':'2026-01-01T00:00:00', 'event':'login_failed'})+'\n')
            with self.assertRaises(ValueError):
                analyze_windowed(p)

    def test_incident_report_count(self):
        from redlab.core import incident_report
        with tempfile.TemporaryDirectory() as d:
            p=Path(d)/'events.jsonl'
            rows=[{'timestamp':f'2026-01-01T00:0{i}:00Z','event':'login_failed','actor':'fiction'} for i in range(3)]
            p.write_text(''.join(json.dumps(x)+'\n' for x in rows))
            self.assertEqual(incident_report(p)['by_rule']['login-failure-burst'],1)
    def test_incident_report_empty_log(self):
        from redlab.core import incident_report
        with tempfile.TemporaryDirectory() as d:
            p=Path(d)/'events.jsonl';p.write_text('')
            self.assertEqual(incident_report(p)['events'],0)
