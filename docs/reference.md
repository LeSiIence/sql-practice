# 数据库与判题说明

## 数据与关系

- Department(Dno PK, Dname UNIQUE, Dean)
- Student(Sno PK, Sname, Ssex, Sage, Dno FK → Department)
- Teacher(Tno PK, Tname UNIQUE, Ttitle, Dno FK → Department)
- Course(Cno PK, Cname UNIQUE, Credit, Cdept FK → Department, Tno FK → Teacher)
- SC(Sno FK → Student, Cno FK → Course, Grade)，联合主键 (Sno,Cno)
- Prerequisite(Cno FK → Course, Pno FK → Course)，联合主键 (Cno,Pno)

六表和列名与图片一致；补充 Prerequisite 的两个课程外键，并约束成绩为 NULL 或 0–100、年龄/学分大于 0、自身不能作为自己的直接先修课。Dean 是姓名文本，图片没有定义其外键。没有额外强制开课系等于教师所属系。

基础数据包含 4 个系、12 名学生、4 名教师、9 门课程、23 条选课、6 条先修关系。包括同名学生、未选课学生、无人选修课程、全部 NULL 成绩课程、跨系授课、先修链、多个先修课程、60 分边界与系内并列第一。

真实 SQLite 数据库位于 `data/practice.db`；`schema.sql` 是建表脚本，`seed.sql` 是可导入的数据脚本。用其他数据库工具连接此文件即可浏览。使用外部 SQLite 连接修改时需自行执行 `PRAGMA foreign_keys=ON`。SQLite 没有 PostgreSQL/MySQL 的完整类型与语法；本环境支持题目列出的集合运算、连接、子查询、CTE 和窗口函数，不支持 `ALL/ANY` 比较量词。聚合查询请遵守标准 SQL 的 GROUP BY 规则，SQLite 本身对裸列较宽松。

## 判题规则

每题在 **23 组可重现数据** 上执行，与独立的 Python 集合/聚合逻辑计算的结果比较，不按 SQL 文本比对。**不检查行顺序及列别名，检查列数、列顺序、每个值和重复行次数**。列顺序在答案文件注释中列出。数值允许浮点误差（绝对 1e-7，相对 1e-9）；不要人为 ROUND 平均分。NULL 与 0、空字符串不同；字符串 `'80'` 与数值 `80` 不同。所有题预期每个实体或组合只出现一次（第 13 题按选课行展开）。

场景包含基础数据、确实存在全选学生与全员及格课程、S1 未选课、目标教师/系无课程、全部 NULL、全体未选课、空学生表、空课程表、均分恰为 80、并列第一、无先修关系及 12 组固定种子的组合数据。使用空集合是为了检验“全部”的逻辑含义。

失败时显示缺少/多出的行（各最多 8 行）。需要复现其他测试数据时，导出第 1–23 组数据到新的文件：

```bash
python lab.py export-case 2 data/case-02.sql
```

导出是包含 DDL 和数据的完整 SQL 脚本，应用到空数据库。场景名称会显示在失败报告中；完整顺序见 `datasets.py`。判题总是在内存中重建固定测试数据，不受你对 `practice.db` 的修改影响。有限测试不能证明对所有可能数据库状态都正确；语义正确性仍需自己推理。

## 题意约定

1–16 题按图片文字；“计算机系”“数据库系统”“张明”是精确名称。选课人数包括 NULL；AVG/MAX 忽略 NULL，全为 NULL 时结果为 NULL。`选修`只要求存在 SC 记录，不要求及格。

- 第 10/11/12/15 题：目标课程集合为空时，全体学生满足“选修全部”；第 12 题包括 S1 本人。
- 第 13 题：输出 Sno,Sname,Cno,Cname,Grade；未选课学生保留一行，后三列为 NULL。
- 第 15 题：以 Course.Cdept 判断开课系。
- 第 16 题：输出 Sno,Sname；排除 S1，只比较课程集合，与成绩无关。
- 第 17 题：输出 Dno,Sno,Sname,AvgGrade；按学生所在系分组，保留并列第一；无有效成绩的学生不参与比较。
- **第 18 题（已确认）**：输出 Sno,Sname；至少选过一门课，且其已选课程的所有**直接**先修课均有成绩 >=60 的 SC 记录；NULL 不算通过。无直接先修课视为满足，不做额外的传递闭包检查。
- 第 19 题：输出 Cno,Cname；全体学生都选修且 Grade>=60；NULL 不算及格。学生表为空时所有课程满足。
- **第 20 题（已确认）**：输出 Sno,Sname,Cno,Cname；尚未选修，且所有**直接**先修课都已及格的课程。无先修课也可推荐；已选但挂科的课不重复推荐。没有推荐课的学生不输出占位行。

## 文件、验证及资源限制

`test.py` 是判题入口；`lab.py` 是辅助命令入口；`questions.py` 存题目；`datasets.py` 存测试数据；`oracle.py` 以 Python 计算预期结果。答案模板不包含参考 SQL。`tests/test_lab.py` 是维护者测试，含验证用 SQL，做题时无需打开。

```bash
python -m unittest discover -s tests -v
```

Windows 原生 Python、WSL 和 Linux 均受支持。查询使用独立进程、只读授权、单场景约 1.2 秒、整次最多 10 秒、2,000 行结果限制。Linux 额外设置 256 MiB 地址空间和 8 秒 CPU 时间上限；Windows 不设置这两项操作系统资源上限，但仍执行查询和进程超时限制。SELECT 和 WITH 查询可用；禁止写表、DDL、PRAGMA、ATTACH 和扩展加载。不启动任何网络服务。SQL 文件使用 UTF-8，子进程通信也使用 UTF-8。

`python lab.py init` 可补建缺少的数据库和答案文件，保留已有答案；它不会覆盖已存在的数据库。若需恢复基础数据，将 `data/practice.db` 重命名备份，再运行 `init`。题目答案在 `answers/`，与数据库独立。
