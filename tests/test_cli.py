"""在临时项目内验证文件判题入口，不改动实际答案。"""
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from test_lab import VALID

ROOT=Path(__file__).resolve().parents[1]


class FileRunnerTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.temp=tempfile.TemporaryDirectory()
        cls.root=Path(cls.temp.name)/'SQL 练习项目'
        cls.root.mkdir()
        for name in ['test.py','lab.py','engine.py','questions.py','datasets.py','oracle.py','schema.sql']:
            shutil.copy2(ROOT/name,cls.root/name)
        (cls.root/'answers').mkdir()

    @classmethod
    def tearDownClass(cls): cls.temp.cleanup()

    def run_cli(self,*args):
        return subprocess.run([sys.executable,str(self.root/'test.py'),*args],
                              cwd=self.temp.name,capture_output=True,text=True,encoding='utf-8',timeout=30)

    def test_init_and_readonly_database_in_unicode_path(self):
        result=subprocess.run([sys.executable,str(self.root/'lab.py'),'init'],
                              cwd=self.temp.name,capture_output=True,text=True,encoding='utf-8',timeout=10)
        self.assertEqual(result.returncode,0,result.stdout+result.stderr)
        result=subprocess.run([sys.executable,str(self.root/'lab.py'),'run','--sql',
                               "SELECT Dname FROM Department WHERE Dname='计算机系'"],
                              cwd=self.temp.name,capture_output=True,text=True,encoding='utf-8',timeout=10)
        self.assertEqual(result.returncode,0,result.stdout+result.stderr)
        self.assertIn('计算机系',result.stdout)

    def test_cli_workflow(self):
        for i,sql in enumerate(VALID,1):
            (self.root/'answers'/f'{i:02}.sql').write_text(sql,encoding='utf-8')
        result=self.run_cli('--all')
        self.assertEqual(result.returncode,0,result.stdout+result.stderr)
        self.assertIn('通过 20/20',result.stdout)
        for n in (1,10,20):
            result=self.run_cli(f'-{n}')
            self.assertEqual(result.returncode,0,result.stdout+result.stderr)
        path=self.root/'answers'/'01.sql'
        path.write_text('SELECT Sno,Sname,Sage FROM Student',encoding='utf-8')
        result=self.run_cli('-1','--verbose')
        self.assertEqual(result.returncode,1)
        self.assertIn('多出的行',result.stdout)
        path.write_text('-- 待填写\n/* 注释 */\n',encoding='utf-8')
        result=self.run_cli('-1')
        self.assertEqual(result.returncode,1)
        self.assertIn('[未作答]',result.stdout)
        result=self.run_cli('--all')
        self.assertEqual(result.returncode,1)
        self.assertIn('通过 19/20',result.stdout)
        path.write_text(VALID[0],encoding='utf-8-sig')
        self.assertEqual(self.run_cli('-1','--file',str(path)).returncode,0)
        path.unlink()
        result=self.run_cli('-1')
        self.assertEqual(result.returncode,1)
        self.assertIn('无法读取',result.stdout)
        for args in [[],['-21'],['-1','--all'],['--all','--file','x.sql']]:
            self.assertEqual(self.run_cli(*args).returncode,2)


if __name__=='__main__': unittest.main()
