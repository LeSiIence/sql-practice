"""可重现的练习数据及边界数据。"""
import copy
import random

TABLES = ['Department','Student','Teacher','Course','SC','Prerequisite']

def base():
    return {
      'Department': [('D1','计算机系','王主任'),('D2','数学系','李主任'),('D3','外语系','赵主任'),('D4','物理系','周主任')],
      'Student': [(f'S{i}',name,'女' if i%2 else '男',18+i%5,d) for i,(name,d) in enumerate([
          ('李华','D1'),('王芳','D1'),('刘洋','D1'),('陈晨','D1'),('赵敏','D2'),('周杰','D2'),
          ('吴桐','D3'),('郑欣','D3'),('孙宁','D4'),('何平','D4'),('李华','D2'),('林晓','D3')],1)],
      'Teacher': [('T1','张明','教授','D1'),('T2','李梅','副教授','D1'),('T3','王强','教授','D2'),('T4','陈静','讲师','D3')],
      'Course': [('C1','数据库系统',4,'D1','T1'),('C2','数据结构',4,'D1','T1'),('C3','程序设计',3,'D1','T2'),
                 ('C4','高等数学',4,'D2','T3'),('C5','大学英语',2,'D3','T4'),('C6','人工智能',3,'D1','T2'),
                 ('C7','学术写作',2,'D3','T4'),('C8','概率论',3,'D2','T2'),('C9','数据库实验',1,'D1','T1')],
      'SC': [('S1','C1',90),('S1','C2',80),('S1','C3',70),
             ('S2','C1',80),('S2','C2',90),('S2','C3',70),
             ('S3','C1',100),('S3','C2',None),('S3','C3',60),('S3','C9',80),
             ('S4','C2',55),('S4','C3',60),('S5','C1',None),('S5','C4',100),
             ('S6','C4',60),('S6','C5',100),('S7','C5',59),('S7','C6',None),
             ('S8','C6',None),('S11','C3',70),('S11','C4',90),('S12','C5',60),('S12','C7',100)],
      'Prerequisite': [('C1','C2'),('C2','C3'),('C6','C1'),('C6','C4'),('C7','C5'),('C9','C1')],
    }

def cases():
    b=base()
    out=[('基础数据',b)]
    d=copy.deepcopy(b)
    enrolled={(s,c) for s,c,g in d['SC']}
    d['SC'] += [('S3',c[0],85) for c in d['Course'] if ('S3',c[0]) not in enrolled]
    for s in d['Student']:
        if (s[0],'C8') not in {(a,c) for a,c,g in d['SC']}:
            d['SC'].append((s[0],'C8',60 if s[0]=='S1' else 90))
    out.append(('全选课程与全员及格',d))
    d=copy.deepcopy(b); d['SC']=[r for r in d['SC'] if r[0]!='S1']; out.append(('S1选课为空',d))
    d=copy.deepcopy(b); d['Course']=[(c,n,cr,'D2','T2') for c,n,cr,dep,t in d['Course']]; out.append(('目标教师与开课系无课程',d))
    d=copy.deepcopy(b); d['SC']=[(s,c,None) for s,c,g in d['SC']]; out.append(('全部成绩未录入',d))
    d=copy.deepcopy(b); d['SC']=[]; out.append(('全体未选课',d))
    d=copy.deepcopy(b); d['SC']=[]; d['Student']=[]; out.append(('学生全集为空',d))
    d=copy.deepcopy(b); d['SC']=[]; d['Course']=[]; d['Prerequisite']=[]; out.append(('课程全集为空',d))
    d=copy.deepcopy(b); d['SC']=[('S1','C1',100),('S2','C1',60),('S3','C2',81),('S4','C2',None),('S5','C4',100),('S6','C6',None)]; out.append(('80分边界及NULL人数',d))
    d=copy.deepcopy(b); d['SC']=[('S1','C1',90),('S2','C1',90),('S3','C1',60),('S4','C1',None)]; out.append(('系内并列与无有效成绩',d))
    d=copy.deepcopy(b); d['Prerequisite']=[]; out.append(('没有先修关系',d))
    for seed in range(12):
        rng=random.Random(1700+seed); d=copy.deepcopy(b)
        d['SC']=[(s[0],c[0],rng.choice([None,0,59,60,75,80,81,90,100])) for s in d['Student'] for c in d['Course'] if rng.random()<.55]
        out.append((f'组合数据{seed+1:02}',d))
    return out

def populate(conn,data):
    for table in TABLES:
        rows=data[table]
        if rows:
            conn.executemany(f'INSERT INTO {table} VALUES ({",".join("?" for _ in rows[0])})',rows)
    conn.commit()
