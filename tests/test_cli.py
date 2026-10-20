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
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory()
        self.root=Path(self.temp.name)/'SQL 练习项目'
        self.root.mkdir()
        for name in ['test.py','lab.py','engine.py','questions.py','datasets.py','oracle.py','schema.sql']:
            shutil.copy2(ROOT/name,self.root/name)
        (self.root/'answers').mkdir()

    def tearDown(self): self.temp.cleanup()

    def run_cli(self,*args):
        return subprocess.run([sys.executable,str(self.root/'test.py'),*args],
                              cwd=self.temp.name,capture_output=True,text=True,encoding='utf-8',timeout=30)

    def test_init_and_readonly_database_in_unicode_path(self):
        result=subprocess.run([sys.executable,str(self.root/'lab.py'),'init'],
                              cwd=self.temp.name,capture_output=True,text=True,encoding='utf-8',timeout=10)
        self.assertEqual(result.returncode,0,result.stdout+result.stderr)
        for number in range(1,25):
            path=self.root/'answers'/f'{number:02}.sql'
            self.assertTrue(path.exists(),path)
            self.assertIn(f'第 {number} 题',path.read_text(encoding='utf-8'))
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
        self.assertIn('通过 24/24',result.stdout)
        for n in (1,10,20,21,22,23,24):
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
        self.assertIn('通过 23/24',result.stdout)
        path.write_text(VALID[0],encoding='utf-8-sig')
        self.assertEqual(self.run_cli('-1','--file',str(path)).returncode,0)
        path.unlink()
        result=self.run_cli('-1')
        self.assertEqual(result.returncode,1)
        self.assertIn('无法读取',result.stdout)
        for args in [[],['-25'],['-1','--all'],['--all','--file','x.sql']]:
            self.assertEqual(self.run_cli(*args).returncode,2)

    def test_lab_question_and_check_commands(self):
        for n in (21,22,23,24):
            for args in [('question',str(n)),('check',str(n),'--sql',VALID[n-1])]:
                with self.subTest(args=args):
                    result=subprocess.run([sys.executable,str(self.root/'lab.py'),*args],
                                          cwd=self.temp.name,capture_output=True,text=True,encoding='utf-8',timeout=10)
                    self.assertEqual(result.returncode,0,result.stdout+result.stderr)
        for i,sql in enumerate(VALID,1):
            (self.root/'answers'/f'{i:02}.sql').write_text(sql,encoding='utf-8')
        result=subprocess.run([sys.executable,str(self.root/'lab.py'),'check-all'],
                              cwd=self.temp.name,capture_output=True,text=True,encoding='utf-8',timeout=30)
        self.assertEqual(result.returncode,0,result.stdout+result.stderr)
        self.assertIn('共通过 24/24 题',result.stdout)


if __name__=='__main__': unittest.main()
