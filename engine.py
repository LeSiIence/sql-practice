import json
import math
import sqlite3
import subprocess
import sys
import time
from pathlib import Path
from datasets import base, cases, populate, TABLES
from oracle import expected
from questions import QUESTIONS

ROOT=Path(__file__).resolve().parent
DB=ROOT/'data'/'practice.db'
WORKER_TIMEOUT=10

def configure_output():
    """Keep Chinese output readable in Windows terminals and redirected pipes."""
    for stream in (sys.stdout,sys.stderr):
        if hasattr(stream,'reconfigure'):
            stream.reconfigure(encoding='utf-8',errors='backslashreplace')

def apply_resource_limits():
    # Windows has no resource module. Wall-clock limits and SQLite's query
    # deadline still apply on every platform; Linux also caps memory and CPU.
    if sys.platform.startswith('linux'):
        import resource
        resource.setrlimit(resource.RLIMIT_AS,(256*1024*1024,256*1024*1024))
        resource.setrlimit(resource.RLIMIT_CPU,(8,8))

def connection(data):
    conn=sqlite3.connect(':memory:')
    conn.executescript((ROOT/'schema.sql').read_text(encoding='utf-8'))
    populate(conn,data)
    return conn

def initialize():
    DB.parent.mkdir(exist_ok=True)
    if not DB.exists():
        con=sqlite3.connect(DB)
        try:
            con.executescript((ROOT/'schema.sql').read_text(encoding='utf-8'))
            populate(con,base())
        finally: con.close()
    answers=ROOT/'answers'; answers.mkdir(exist_ok=True)
    for q in QUESTIONS:
        path=answers/f'{q["id"]:02}.sql'
        if not path.exists():
            path.write_text(f'-- 第 {q["id"]} 题：{q["title"]}\n-- 输出列顺序：{", ".join(q["columns"])}\n-- {q["note"]}\n\n',encoding='utf-8')

def query(conn,sql):
    if not sql.strip() or len(sql)>20000: raise ValueError('请输入 SQL，最多 20,000 个字符。')
    allowed={sqlite3.SQLITE_SELECT,sqlite3.SQLITE_READ,sqlite3.SQLITE_FUNCTION,sqlite3.SQLITE_RECURSIVE}
    def authorize(action,arg1,arg2,db,source):
        if action not in allowed: return sqlite3.SQLITE_DENY
        if action==sqlite3.SQLITE_READ and arg1 not in TABLES: return sqlite3.SQLITE_DENY
        if action==sqlite3.SQLITE_FUNCTION and (arg2 or '').lower() in ('load_extension','readfile','writefile','randomblob','zeroblob'): return sqlite3.SQLITE_DENY
        return sqlite3.SQLITE_OK
    conn.set_authorizer(authorize)
    deadline=time.monotonic()+1.2
    conn.set_progress_handler(lambda: int(time.monotonic()>deadline),1000)
    try:
        cur=conn.execute(sql)
        if cur.description is None: raise ValueError('仅允许 SELECT / WITH 查询。')
        rows=cur.fetchmany(2001)
        if len(rows)>2000: raise ValueError('结果超过 2,000 行，请检查是否缺少连接条件。')
        return [c[0] for c in cur.description],rows
    finally:
        conn.set_authorizer(None); conn.set_progress_handler(None,0)

def row_equal(a,b):
    if len(a)!=len(b): return False
    for x,y in zip(a,b):
        if isinstance(x,(int,float)) and isinstance(y,(int,float)):
            if not math.isclose(x,y,rel_tol=1e-9,abs_tol=1e-7): return False
        elif x!=y: return False
    return True

def diff(actual,want):
    # Bipartite matching preserves duplicate multiplicity and numeric tolerance.
    match={}
    def augment(i,seen):
        for j,row in enumerate(want):
            if j not in seen and row_equal(actual[i],row):
                seen.add(j)
                if j not in match or augment(match[j],seen):
                    match[j]=i; return True
        return False
    for i in range(len(actual)): augment(i,set())
    matched=set(match.values())
    return [r for j,r in enumerate(want) if j not in match], [r for i,r in enumerate(actual) if i not in matched]

def work(job):
    sql=job['sql']
    if job['action']=='run':
        conn=sqlite3.connect(DB.as_uri()+'?mode=ro',uri=True)
        try: cols,rows=query(conn,sql)
        finally: conn.close()
        return dict(ok=True,columns=cols,rows=rows,count=len(rows))
    q=int(job['question'])
    if not 1<=q<=20: raise ValueError('题号必须为 1–20')
    results=[]
    for name,data in cases():
        conn=connection(data)
        try:
            cols,actual=query(conn,sql); want=expected(q,data)
            if len(cols)!=len(QUESTIONS[q-1]['columns']):
                results.append(dict(name=name,ok=False,error=f'列数不对：需要 {len(QUESTIONS[q-1]["columns"])} 列，实际 {len(cols)} 列。'))
            else:
                missing,extra=diff(actual,want)
                results.append(dict(name=name,ok=not(missing or extra),expectedCount=len(want),actualCount=len(actual),missing=missing[:8],extra=extra[:8]))
        except (sqlite3.Error,sqlite3.Warning,ValueError) as exc:
            results.append(dict(name=name,ok=False,error=str(exc)))
        finally: conn.close()
    return dict(ok=all(r['ok'] for r in results),passed=sum(r['ok'] for r in results),total=len(results),cases=results)

def execute(job):
    try:
        proc=subprocess.run([sys.executable,'-X','utf8',str(ROOT/'engine.py')],input=json.dumps(job),text=True,encoding='utf-8',capture_output=True,timeout=WORKER_TIMEOUT,cwd=ROOT)
        if proc.returncode: return dict(ok=False,error='查询进程超出资源限制或执行失败。请缩小查询。')
        return json.loads(proc.stdout)
    except subprocess.TimeoutExpired: return dict(ok=False,error='查询超时（总时限 10 秒）。')
    except (ValueError,OSError) as exc: return dict(ok=False,error=str(exc))

if __name__=='__main__':
    configure_output()
    try:
        apply_resource_limits()
        result=work(json.load(sys.stdin))
    except Exception as exc: result=dict(ok=False,error=str(exc) or type(exc).__name__)
    print(json.dumps(result,ensure_ascii=False))
