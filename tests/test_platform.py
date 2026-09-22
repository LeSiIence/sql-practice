"""Cross-platform worker transport and process limits."""
import builtins
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
import engine


class PlatformTests(unittest.TestCase):
    def test_windows_does_not_import_resource(self):
        original=builtins.__import__
        def guarded(name,*args,**kwargs):
            if name=='resource': raise AssertionError('Windows must not import resource')
            return original(name,*args,**kwargs)
        with patch.object(sys,'platform','win32'),patch('builtins.__import__',side_effect=guarded):
            engine.apply_resource_limits()

    def test_utf8_worker_result(self):
        engine.initialize()
        result=engine.execute(dict(action='run',sql="SELECT '中文🙂' AS label"))
        self.assertTrue(result['ok'],result)
        self.assertEqual(result['rows'],[['中文🙂']])

    def test_worker_deadline_terminates_process(self):
        with tempfile.TemporaryDirectory(prefix='sql-worker-') as temp:
            root=Path(temp)
            (root/'engine.py').write_text('import time\ntime.sleep(30)\n',encoding='utf-8')
            with patch.object(engine,'ROOT',root),patch.object(engine,'WORKER_TIMEOUT',0.2):
                result=engine.execute(dict(action='run',sql='SELECT 1'))
            self.assertFalse(result['ok'])
            self.assertIn('查询超时',result['error'])

    def test_query_timeout_in_worker(self):
        engine.initialize()
        result=engine.execute(dict(action='run',sql='WITH RECURSIVE t(x) AS (VALUES(1) UNION ALL SELECT x+1 FROM t) SELECT SUM(x) FROM t'))
        self.assertFalse(result['ok'])
        self.assertIn('interrupted',result['error'])


if __name__=='__main__': unittest.main()
