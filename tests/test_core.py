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
