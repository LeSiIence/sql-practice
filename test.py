#!/usr/bin/env python3
"""从 answers/01.sql … answers/20.sql 读取答案并判题。"""
import argparse
import json
import re
from pathlib import Path
from engine import ROOT, execute
from questions import QUESTIONS


def has_sql(sql):
    without_comments = re.sub(r'/\*.*?\*/|--[^\r\n]*', '', sql, flags=re.S)
    return bool(without_comments.strip(' \t\r\n;\ufeff'))


def display_failure(result, columns, verbose):
    if result.get('error'):
        print('  错误：' + result['error'])
        return
    failures = [case for case in result.get('cases', []) if not case['ok']]
    for case in (failures if verbose else failures[:1]):
        print('  失败场景：' + case['name'])
        if case.get('error'):
            print('  错误：' + case['error'])
        else:
            print('  输出列顺序：' + ', '.join(columns))
            print(f'  期望 {case["expectedCount"]} 行，实际 {case["actualCount"]} 行')
            print('  缺少的行：' + json.dumps(case['missing'], ensure_ascii=False))
            print('  多出的行：' + json.dumps(case['extra'], ensure_ascii=False))
    if len(failures) > 1 and not verbose:
        print(f'  另有 {len(failures)-1} 组失败；加 --verbose 查看全部。')


def main(argv=None):
    parser = argparse.ArgumentParser(
        description='编辑 answers/NN.sql 后测试；每题检查 23 组数据。',
        epilog='示例：python3 test.py -1 | python3 test.py -20 | python3 test.py --all')
    group = parser.add_mutually_exclusive_group(required=True)
    for q in QUESTIONS:
        group.add_argument(f'-{q["id"]}', dest='number', action='store_const',
                           const=q['id'], help=f'测试第 {q["id"]} 题：answers/{q["id"]:02}.sql')
    group.add_argument('--all', action='store_true', help='测试全部 20 个答案文件')
    parser.add_argument('--verbose', '-v', action='store_true', help='显示每个失败场景的详情')
    parser.add_argument('--file', type=Path, help='单题测试时指定其他 SQL 文件')
    args = parser.parse_args(argv)
    if args.all and args.file:
        parser.error('--file 只能与单题参数（如 -1）一起使用')
    numbers = range(1,21) if args.all else [args.number]
    stats = dict(passed=0, failed=0, blank=0)
    for number in numbers:
        q = QUESTIONS[number-1]
        path = args.file if args.file is not None else ROOT/'answers'/f'{number:02}.sql'
        print(f'\n第 {number:02} 题：{q["title"]}', flush=True)
        try:
            sql = path.read_text(encoding='utf-8-sig')
        except (OSError, UnicodeError) as exc:
            print(f'[错误] 无法读取 {path}：{exc}')
            stats['failed'] += 1
            continue
        if not has_sql(sql):
            print(f'[未作答] 请编辑 {path}')
            stats['blank'] += 1
            continue
        result = execute(dict(action='check', question=number, sql=sql))
        if result['ok']:
            print(f'[通过] {result["passed"]}/{result["total"]} 组数据')
            stats['passed'] += 1
        else:
            stats['failed'] += 1
            print(f'[未通过] {result.get("passed",0)}/{result.get("total",23)} 组数据')
            display_failure(result, q['columns'], args.verbose)
    total = sum(stats.values())
    print(f'\n汇总：通过 {stats["passed"]}/{total}，未通过/错误 {stats["failed"]}，未作答 {stats["blank"]}')
    return 0 if stats['passed'] == total else 1


if __name__ == '__main__':
    raise SystemExit(main())
