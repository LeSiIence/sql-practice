"""用 Python 集合与聚合计算期望结果，不向用户提供 SQL 答案。"""
def expected(q,d):
    students=d['Student']; courses=d['Course']; sc=d['SC']
    deps={r[0]:r[1] for r in d['Department']}
    teachers={r[0]:r[1] for r in d['Teacher']}
    cs={r[0]:r for r in courses}
    selected={s[0]:{c for sn,c,g in sc if sn==s[0]} for s in students}
    grades={(s,c):g for s,c,g in sc}
    prereq={c[0]:{p for cn,p in d['Prerequisite'] if cn==c[0]} for c in courses}
    def avg(values):
        v=[x for x in values if x is not None]
        return sum(v)/len(v) if v else None
    def passed(s,c): return grades.get((s,c)) is not None and grades[s,c]>=60
    def people(pred): return [(s[0],s[1]) for s in students if pred(s[0])]
    db={c[0] for c in courses if c[1]=='数据库系统'}
    if q==1: return [(s[0],s[1],s[3]) for s in students if deps[s[4]]=='计算机系']
    if q==2: return [(s[0],s[1],g) for s in students for sn,c,g in sc if sn==s[0] and c in db]
    if q==3: return [(s[0],) for s in students if selected[s[0]] & {'C1','C2'}]
    if q==4: return [(s[0],) for s in students if 'C1' in selected[s[0]] and 'C2' not in selected[s[0]]]
    if q==5: return [(s[0],) for s in students if {'C1','C2'} <= selected[s[0]]]
    if q==6: return people(lambda s:not selected[s])
    if q in (7,8):
        result=[]
        for c in courses:
            gs=[g for s,cn,g in sc if cn==c[0]]; mean=avg(gs)
            if q==7 and gs: result.append((c[0],len(gs),mean,max((g for g in gs if g is not None),default=None)))
            if q==8 and len(gs)>=2 and mean is not None and mean>80: result.append((c[0],c[1],mean))
        return result
    if q==9:
        mean=avg([g for s,c,g in sc if c in db])
        return [(s[0],s[1],g) for s in students for sn,c,g in sc if sn==s[0] and c in db and g is not None and mean is not None and g>mean]
    if q in (10,11,12,15):
        target=({c[0] for c in courses if teachers[c[4]]=='张明'} if q==10 else
                set(cs) if q==11 else selected.get('S1',set()) if q==12 else
                {c[0] for c in courses if deps[c[3]]=='计算机系'})
        return people(lambda s:target<=selected[s])
    if q==13:
        return [row for s in students for row in
                ([(s[0],s[1],c,cs[c][1],grades[s[0],c]) for c in sorted(selected[s[0]])] or [(s[0],s[1],None,None,None)])]
    if q==14: return [(c[0],c[1]) for c in courses if not any(c[0] in v for v in selected.values())]
    if q==16: return people(lambda s:s!='S1' and selected[s]==selected.get('S1',set()))
    if q==17:
        means={s[0]:avg([g for sn,c,g in sc if sn==s[0]]) for s in students}
        tops={dep:max((means[s[0]] for s in students if s[4]==dep and means[s[0]] is not None),default=None) for dep in deps}
        return [(s[4],s[0],s[1],means[s[0]]) for s in students if means[s[0]] is not None and means[s[0]]==tops[s[4]]]
    if q==18: return people(lambda s:bool(selected[s]) and all(passed(s,p) for c in selected[s] for p in prereq[c]))
    if q==19: return [(c[0],c[1]) for c in courses if all(passed(s[0],c[0]) for s in students)]
    if q==20: return [(s[0],s[1],c[0],c[1]) for s in students for c in courses if c[0] not in selected[s[0]] and all(passed(s[0],p) for p in prereq[c[0]])]
    raise ValueError('题号必须为 1–20')
