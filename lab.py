#!/usr/bin/env python3
import argparse
import json
import sys
from datasets import cases
from engine import ROOT, DB, initialize, connection, execute
from questions import QUESTIONS

def show(result):
    if result.get('error'): print('错误：',result['error']); return
    if 'cases' in result:
        print(f'{"通过" if result["ok"] else "未通过"}：{result["passed"]}/{result["total"]} 组数据')
        for c in result['cases']:
            if not c['ok']:
                print('\n失败场景：'+c['name'])
                if c.get('error'): print(c['error'])
                else:
                    print('缺少的行：',json.dumps(c['missing'],ensure_ascii=False))
                    print('多出的行：',json.dumps(c['extra'],ensure_ascii=False))
    else:
        print(' | '.join(result['columns']))
        for row in result['rows']: print(' | '.join('NULL' if v is None else str(v) for v in row))
        print(f'共 {result["count"]} 行')

def main():
    parser=argparse.ArgumentParser(description='高校教学数据库 SQL 实战环境')
    sub=parser.add_subparsers(dest='command',required=True)
    sub.add_parser('init'); sub.add_parser('list'); sub.add_parser('schema')
    p=sub.add_parser('question'); p.add_argument('number',type=int,choices=range(1,21))
    p=sub.add_parser('run'); g=p.add_mutually_exclusive_group(required=True); g.add_argument('--sql'); g.add_argument('--file')
    p=sub.add_parser('check'); p.add_argument('number',type=int,choices=range(1,21)); p.add_argument('--file'); p.add_argument('--sql')
    sub.add_parser('check-all')
    p=sub.add_parser('export-case'); p.add_argument('number',type=int,choices=range(1,len(cases())+1)); p.add_argument('output')
    args=parser.parse_args(); initialize()
    if args.command=='init': print(f'数据库已就绪：{DB}\n答案目录：{ROOT / "answers"}（保留已有答案）')
    elif args.command=='list':
        for q in QUESTIONS: print(f'{q["id"]:02}. {q["title"]}')
    elif args.command=='schema': print((ROOT/'schema.sql').read_text())
    elif args.command=='question':
        q=QUESTIONS[args.number-1]; print(q['title']+'\n输出列顺序：'+', '.join(q['columns'])+'\n'+q['note'])
    elif args.command in ('run','check'):
        if args.sql is not None: sql=args.sql
        else:
            path=__import__('pathlib').Path(args.file) if args.file else ROOT/'answers'/f'{args.number:02}.sql'
            sql=path.read_text(encoding='utf-8')
        result=execute(dict(action=args.command,sql=sql,question=getattr(args,'number',None))); show(result)
        sys.exit(0 if result['ok'] else 1)
    elif args.command=='check-all':
        passed=0
        for q in QUESTIONS:
            result=execute(dict(action='check',sql=(ROOT/'answers'/f'{q["id"]:02}.sql').read_text(encoding='utf-8'),question=q['id']))
            passed+=int(result['ok']); print(f'第 {q["id"]:02} 题：'+('通过' if result['ok'] else '未通过'))
        print(f'共通过 {passed}/20 题'); sys.exit(0 if passed==20 else 1)
    elif args.command=='export-case':
        from pathlib import Path
        name,data=cases()[args.number-1]; conn=connection(data)
        with Path(args.output).open('x',encoding='utf-8') as f: f.write('\n'.join(conn.iterdump())+'\n')
        conn.close(); print('已导出：'+name)

if __name__=='__main__': main()
