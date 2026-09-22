"""维护者回归测试；含验证用 SQL，做题时无需阅读本文件。"""
import sqlite3
import sys
import unittest
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from datasets import base,cases
from engine import connection,query,diff,execute,initialize
from oracle import expected

VALID = [
 "SELECT Sno,Sname,Sage FROM Student JOIN Department USING(Dno) WHERE Dname='计算机系'",
 "SELECT s.Sno,Sname,Grade FROM Student s JOIN SC ON s.Sno=SC.Sno JOIN Course USING(Cno) WHERE Cname='数据库系统'",
 "SELECT Sno FROM SC WHERE Cno='C1' UNION SELECT Sno FROM SC WHERE Cno='C2'",
 "SELECT Sno FROM SC WHERE Cno='C1' EXCEPT SELECT Sno FROM SC WHERE Cno='C2'",
 "SELECT Sno FROM SC WHERE Cno='C1' INTERSECT SELECT Sno FROM SC WHERE Cno='C2'",
 "SELECT Sno,Sname FROM Student s WHERE NOT EXISTS(SELECT 1 FROM SC WHERE Sno=s.Sno)",
 "SELECT Cno,COUNT(*),AVG(Grade),MAX(Grade) FROM SC GROUP BY Cno",
 "SELECT c.Cno,Cname,AVG(Grade) FROM Course c JOIN SC ON c.Cno=SC.Cno GROUP BY c.Cno,Cname HAVING AVG(Grade)>80 AND COUNT(*)>=2",
 "SELECT s.Sno,Sname,Grade FROM Student s JOIN SC ON s.Sno=SC.Sno JOIN Course c ON c.Cno=SC.Cno WHERE Cname='数据库系统' AND Grade>(SELECT AVG(x.Grade) FROM SC x WHERE x.Cno=c.Cno)",
 "SELECT Sno,Sname FROM Student s WHERE NOT EXISTS(SELECT 1 FROM Course c JOIN Teacher t ON c.Tno=t.Tno WHERE Tname='张明' AND NOT EXISTS(SELECT 1 FROM SC WHERE Sno=s.Sno AND Cno=c.Cno))",
 "SELECT Sno,Sname FROM Student s WHERE NOT EXISTS(SELECT 1 FROM Course c WHERE NOT EXISTS(SELECT 1 FROM SC WHERE Sno=s.Sno AND Cno=c.Cno))",
 "SELECT Sno,Sname FROM Student s WHERE NOT EXISTS(SELECT 1 FROM SC x WHERE x.Sno='S1' AND NOT EXISTS(SELECT 1 FROM SC y WHERE y.Sno=s.Sno AND y.Cno=x.Cno))",
 "SELECT s.Sno,Sname,c.Cno,Cname,Grade FROM Student s LEFT JOIN SC ON s.Sno=SC.Sno LEFT JOIN Course c ON c.Cno=SC.Cno",
 "SELECT Cno,Cname FROM Course c WHERE NOT EXISTS(SELECT 1 FROM SC WHERE Cno=c.Cno)",
 "SELECT Sno,Sname FROM Student s WHERE NOT EXISTS(SELECT 1 FROM Course c JOIN Department d ON c.Cdept=d.Dno WHERE Dname='计算机系' AND NOT EXISTS(SELECT 1 FROM SC WHERE Sno=s.Sno AND Cno=c.Cno))",
 "SELECT Sno,Sname FROM Student s WHERE Sno<>'S1' AND NOT EXISTS(SELECT Cno FROM SC WHERE Sno='S1' EXCEPT SELECT Cno FROM SC WHERE Sno=s.Sno) AND NOT EXISTS(SELECT Cno FROM SC WHERE Sno=s.Sno EXCEPT SELECT Cno FROM SC WHERE Sno='S1')",
 "WITH a AS (SELECT s.Dno,s.Sno,s.Sname,AVG(Grade) AS m FROM Student s JOIN SC ON s.Sno=SC.Sno GROUP BY s.Dno,s.Sno,s.Sname) SELECT Dno,Sno,Sname,m FROM a WHERE m=(SELECT MAX(b.m) FROM a b WHERE b.Dno=a.Dno)",
 "SELECT Sno,Sname FROM Student s WHERE EXISTS(SELECT 1 FROM SC WHERE Sno=s.Sno) AND NOT EXISTS(SELECT 1 FROM SC x JOIN Prerequisite p ON x.Cno=p.Cno WHERE x.Sno=s.Sno AND NOT EXISTS(SELECT 1 FROM SC y WHERE y.Sno=s.Sno AND y.Cno=p.Pno AND y.Grade>=60))",
 "SELECT Cno,Cname FROM Course c WHERE NOT EXISTS(SELECT 1 FROM Student s WHERE NOT EXISTS(SELECT 1 FROM SC WHERE Sno=s.Sno AND Cno=c.Cno AND Grade>=60))",
 "SELECT s.Sno,Sname,c.Cno,Cname FROM Student s CROSS JOIN Course c WHERE NOT EXISTS(SELECT 1 FROM SC WHERE Sno=s.Sno AND Cno=c.Cno) AND NOT EXISTS(SELECT 1 FROM Prerequisite p WHERE p.Cno=c.Cno AND NOT EXISTS(SELECT 1 FROM SC WHERE Sno=s.Sno AND Cno=p.Pno AND Grade>=60))",
]

class LabTests(unittest.TestCase):
    def test_all_20_queries_on_all_23_cases(self):
        for name,data in cases():
            con=connection(data)
            self.assertEqual(con.execute('PRAGMA foreign_key_check').fetchall(),[])
            for q,sql in enumerate(VALID,1):
                with self.subTest(case=name,q=q):
                    cols,rows=query(con,sql)
                    self.assertEqual(diff(rows,expected(q,data)),([],[]))
            con.close()

    def test_oracle_anchors(self):
        d=base()
        self.assertEqual(expected(4,d),[('S5',)])
        self.assertEqual(expected(16,d),[('S2','王芳')])
        self.assertEqual(expected(11,d),[])
        self.assertEqual(expected(19,d),[])
        self.assertEqual(set(expected(14,d)),{('C8','概率论')})
        self.assertIn(('C6',2,None,None),expected(7,d))
        self.assertIn(('D1','S1','李华',80.0),expected(17,d))
        self.assertIn(('D1','S2','王芳',80.0),expected(17,d))

    def test_bad_queries_rejected_by_cases(self):
        wrong=[(3,"SELECT Sno FROM SC WHERE Cno IN ('C1','C2')"),
               (7,"SELECT Cno,COUNT(Grade),AVG(Grade),MAX(Grade) FROM SC GROUP BY Cno"),
               (8,VALID[7].replace('>80','>=80')),
               (12,VALID[11]+" AND s.Sno<>'S1'"),
               (17,VALID[16]+" LIMIT 1"),
               (18,VALID[17].replace('y.Grade>=60','(y.Grade>=60 OR y.Grade IS NULL)')),
               (20,VALID[19].replace('Grade>=60','Grade>60'))]
        for q,sql in wrong:
            failures=0
            for _,d in cases():
                con=connection(d); cols,rows=query(con,sql); con.close()
                missing,extra=diff(rows,expected(q,d)); failures+=bool(missing or extra)
            self.assertGreater(failures,0,(q,sql))

    def test_constraints(self):
        con=connection(base())
        for sql in ["INSERT INTO SC VALUES ('missing','C1',90)","INSERT INTO SC VALUES ('S1','C1',90)","INSERT INTO SC VALUES ('S1','C8',101)","INSERT INTO Prerequisite VALUES ('C1','missing')"]:
            with self.assertRaises(sqlite3.IntegrityError): con.execute(sql)
        con.close()

    def test_read_only_and_limits(self):
        con=connection(base())
        for sql in ["DELETE FROM Student","DROP TABLE SC","ATTACH DATABASE ':memory:' AS other","PRAGMA table_info(Student)","SELECT * FROM sqlite_master","SELECT 1; SELECT 2","SELECT load_extension('x')"]:
            with self.assertRaises((sqlite3.Error,sqlite3.Warning,ValueError)): query(con,sql)
        with self.assertRaises(sqlite3.Error): query(con,'WITH RECURSIVE t(x) AS (VALUES(1) UNION ALL SELECT x+1 FROM t) SELECT SUM(x) FROM t')
        con.close()

    def test_multiset_comparison(self):
        self.assertEqual(diff([(None,1.0),('a',2)], [('a',2.0),(None,1)]),([],[]))
        self.assertNotEqual(diff([(1,),(1,)],[(1,)]),([],[]))
        self.assertNotEqual(diff([('1',)],[(1,)]),([],[]))

    def test_subprocess(self):
        initialize()
        self.assertTrue(execute(dict(action='check',question=1,sql=VALID[0]))['ok'])
        self.assertFalse(execute(dict(action='check',question=1,sql='SELECT 1 WHERE 0'))['ok'])
        self.assertTrue(execute(dict(action='run',sql='SELECT * FROM Student'))['ok'])

if __name__=='__main__': unittest.main(verbosity=2)
