"""维护者回归测试；含验证用 SQL，做题时无需阅读本文件。"""
import sqlite3
import sys
import unittest
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from datasets import base,cases
from engine import connection,query,diff,execute,initialize
from oracle import expected
from questions import QUESTIONS

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
 "WITH ranked AS (SELECT Cno,Sno,Grade,DENSE_RANK() OVER (PARTITION BY Cno ORDER BY Grade DESC) AS place FROM SC WHERE Grade IS NOT NULL) SELECT c.Cno,c.Cname,s.Sno,s.Sname,r.Grade FROM ranked r JOIN Course c ON c.Cno=r.Cno JOIN Student s ON s.Sno=r.Sno WHERE r.place=2",
 "SELECT Sno,Sname FROM Student s WHERE EXISTS(SELECT 1 FROM SC WHERE Sno=s.Sno) AND NOT EXISTS(SELECT 1 FROM SC WHERE Sno=s.Sno AND (Grade<60 OR Grade IS NULL))",
 "WITH credits AS (SELECT s.Dno,s.Sno,s.Sname,COALESCE(SUM(c.Credit),0) AS total FROM Student s LEFT JOIN SC ON s.Sno=SC.Sno LEFT JOIN Course c ON c.Cno=SC.Cno GROUP BY s.Dno,s.Sno,s.Sname) SELECT Dno,Sno,Sname,total FROM credits a WHERE total=(SELECT MAX(b.total) FROM credits b WHERE b.Dno=a.Dno)",
 "SELECT c.Cno,c.Cname,COUNT(p.Cno) FROM Course c LEFT JOIN Prerequisite p ON p.Pno=c.Cno GROUP BY c.Cno,c.Cname",
]

class LabTests(unittest.TestCase):
    def test_all_queries_on_all_cases(self):
        self.assertEqual(len(VALID),len(QUESTIONS))
        for name,data in cases():
            con=connection(data)
            self.assertEqual(con.execute('PRAGMA foreign_key_check').fetchall(),[])
            for q,sql in enumerate(VALID,1):
                with self.subTest(case=name,q=q):
                    cols,rows=query(con,sql)
                    self.assertEqual(len(cols),len(QUESTIONS[q-1]['columns']))
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
        self.assertEqual(set(expected(21,d)),{
            ('C1','数据库系统','S1','李华',90),('C2','数据结构','S1','李华',80),
            ('C3','程序设计','S3','刘洋',60),('C3','程序设计','S4','陈晨',60),
            ('C4','高等数学','S11','李华',90),('C5','大学英语','S12','林晓',60)})
        self.assertEqual(set(expected(22,d)),{('S1','李华'),('S2','王芳'),('S6','周杰'),('S11','李华'),('S12','林晓')})
        self.assertEqual(set(expected(23,d)),{('D1','S3','刘洋',12),('D2','S5','赵敏',8),
                                              ('D3','S7','吴桐',5),('D4','S9','孙宁',0),('D4','S10','何平',0)})
        self.assertEqual({c:count for c,name,count in expected(24,d)},
                         {'C1':2,'C2':1,'C3':1,'C4':1,'C5':1,'C6':0,'C7':0,'C8':0,'C9':0})

    def test_new_question_edge_cases(self):
        data=dict(cases())
        self.assertEqual(set(expected(21,data['不同分数第二高与并列'])),{
            ('C1','数据库系统','S3','刘洋',90),('C1','数据库系统','S4','陈晨',90),
            ('C3','程序设计','S1','李华',0)})
        self.assertEqual(set(expected(22,data['全科及格与NULL及未选课'])),{('S1','李华'),('S5','赵敏')})
        self.assertEqual(set(expected(23,data['总学分并列与同分学分及小数'])),{
            ('D1','S1','李华',5),('D1','S2','王芳',5),('D2','S6','周杰',2.5),
            ('D3','S7','吴桐',2.5),('D3','S8','郑欣',2.5),('D4','S9','孙宁',0),('D4','S10','何平',0)})
        self.assertEqual({c:count for c,name,count in expected(24,data['直接依赖方向与多先修及先修链'])},
                         {'C1':2,'C2':2,'C3':1,'C4':0,'C5':0,'C6':0,'C7':0,'C8':0,'C9':0})
        self.assertEqual(expected(21,data['全部成绩未录入']),[])
        self.assertEqual(expected(22,data['全体未选课']),[])
        self.assertEqual(len(expected(23,data['全体未选课'])),len(base()['Student']))
        self.assertEqual(expected(23,data['学生全集为空']),[])
        self.assertEqual(expected(24,data['课程全集为空']),[])

    def test_bad_queries_rejected_by_cases(self):
        wrong=[(3,"SELECT Sno FROM SC WHERE Cno IN ('C1','C2')"),
               (7,"SELECT Cno,COUNT(Grade),AVG(Grade),MAX(Grade) FROM SC GROUP BY Cno"),
               (8,VALID[7].replace('>80','>=80')),
               (12,VALID[11]+" AND s.Sno<>'S1'"),
               (17,VALID[16]+" LIMIT 1"),
               (18,VALID[17].replace('y.Grade>=60','(y.Grade>=60 OR y.Grade IS NULL)')),
               (20,VALID[19].replace('Grade>=60','Grade>60')),
               (21,VALID[20].replace('DENSE_RANK()','RANK()')),
               (21,VALID[20].replace('DENSE_RANK()','ROW_NUMBER()')),
               (21,VALID[20].replace(' WHERE Grade IS NOT NULL','')),
               (22,VALID[21].replace('Grade<60 OR Grade IS NULL','Grade<60')),
               (22,VALID[21].replace('Grade<60','Grade<=60')),
               (22,VALID[21].replace('EXISTS(SELECT 1 FROM SC WHERE Sno=s.Sno) AND ','')),
               (23,VALID[22].replace('SUM(c.Credit)','SUM(DISTINCT c.Credit)')),
               (23,VALID[22].replace('SUM(c.Credit)','COUNT(c.Cno)')),
               (23,VALID[22].replace('LEFT JOIN SC','JOIN SC')),
               (23,VALID[22].replace('GROUP BY s.Dno','WHERE SC.Grade>=60 GROUP BY s.Dno')),
               (23,VALID[22]+' LIMIT 1'),
               (24,VALID[23].replace('p.Pno=c.Cno','p.Cno=c.Cno')),
               (24,VALID[23].replace('COUNT(p.Cno)','COUNT(*)')),
               (24,VALID[23].replace('LEFT JOIN','JOIN'))]
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
        for q in range(21,len(QUESTIONS)+1):
            with self.subTest(q=q):
                self.assertTrue(execute(dict(action='check',question=q,sql=VALID[q-1]))['ok'])
        self.assertFalse(execute(dict(action='check',question=1,sql='SELECT 1 WHERE 0'))['ok'])
        self.assertTrue(execute(dict(action='run',sql='SELECT * FROM Student'))['ok'])

if __name__=='__main__': unittest.main(verbosity=2)
