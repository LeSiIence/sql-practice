# SQL Practice · 高校教学数据库练习

在 VS Code 中编写 SQL，在终端逐题判定结果。包含 6 张关联表、20 道题和 23 组可重现测试数据，不需要网页或数据库服务。

## 环境要求

- WSL Ubuntu 或 Linux。判题使用 `resource` 限制查询资源，不支持直接在 Windows Python 中运行。
- Python >=3.10；`environment.yml` 配置 Python 3.11 和 SQLite >=3.37。
- 仅使用 Python 标准库，无第三方 pip 依赖，也无需执行 pip 安装命令。

## 快速开始

在 WSL/Linux 终端执行：

```bash
mkdir -p ~/workspace
cd ~/workspace
git clone https://github.com/LeSiIence/sql-practice.git
cd sql-practice
conda env create -f environment.yml
conda activate sql-practice
python lab.py init
code .
```

已有本地项目和 Conda 环境时，只需进入项目并执行 `conda activate sql-practice`，不用再次克隆或创建环境。若当前终端无法使用 `conda activate`，先加载 Conda 的 shell 脚本，例如 Miniconda 默认安装位置下的 `source ~/miniconda3/etc/profile.d/conda.sh`。

`init` 生成 `data/practice.db` 和 `answers/01.sql`～`answers/20.sql`；已存在的数据库和答案不会被覆盖。环境安装后，练习和判题均可离线运行。

## 编辑与测试

每个答案文件开头包含题目和输出列顺序。编辑后先保存，再测试：

```bash
python test.py -1            # 测试 answers/01.sql
python test.py -10           # 测试第 10 题
python test.py -20           # 测试第 20 题
python test.py --all         # 测试全部 20 题
python test.py -1 --verbose  # 展示所有失败场景
```

每题执行 23 组数据，默认显示首个失败场景和缺少/多出的行。空白或只有注释的文件显示“未作答”；`--all` 继续检查其余题目并汇总。退出码：全部通过为 `0`，未通过、未作答或文件错误为 `1`，参数错误为 `2`。

**判题忽略行顺序与列别名，检查列顺序、值和重复行次数。** NULL 不等于 0；不要提前对平均分四舍五入。有限测试不能证明查询对所有可能数据都等价，仍需结合题意判断。

VS Code 以 WSL 模式打开项目。在终端激活环境；如使用 Python 扩展，运行 **Python: Select Interpreter**，选择 `sql-practice`。可以通过 `python -c "import sys; print(sys.executable)"` 确认当前解释器。

## 查看题目、数据和结果

```bash
python lab.py list
python lab.py question 1
python lab.py schema
python lab.py run --sql 'SELECT * FROM Student'
python lab.py run --file answers/01.sql
python test.py -1 --file /path/to/my-answer.sql
python lab.py export-case 2 /tmp/case-02.sql
```

表结构、外键、数据说明、20 题的判题约定以及第 18/20 题的直接先修课定义，见 [数据库与判题说明](docs/reference.md)。完整题目也可用 `python lab.py list` 查看。

## 项目结构

```text
sql-practice/
├── test.py             # 日常判题入口：-1 … -20 / --all
├── lab.py              # 初始化、查看题目、运行 SQL、导出数据
├── engine.py           # 查询执行、资源限制、结果比较
├── questions.py        # 20 道题及输出要求
├── datasets.py         # 基础数据与边界场景
├── oracle.py           # 使用 Python 计算期望结果
├── schema.sql          # 建表及约束
├── seed.sql            # 可导入空表的基础数据
├── environment.yml     # Conda 环境配置
├── docs/reference.md   # 数据库与判题详细说明
├── tests/              # 维护者回归测试
├── answers/            # init 生成；个人答案，不提交 Git
└── data/               # init 生成；本地数据库，不提交 Git
```

个人答案、数据库、缓存和运行日志均由 `.gitignore` 排除，保留在本地。克隆仓库后先运行 `python lab.py init` 生成练习文件。

## 维护与验证

```bash
python -m unittest discover -s tests -v
```

回归测试覆盖 20 题 × 23 组数据、常见错误 SQL、外键约束、只读与超时限制，以及命令行工作流。`tests/test_lab.py` 含验证用 SQL，想独立练习时无需阅读。

若需恢复基础数据库，先将 `data/practice.db` 重命名备份，再运行 `python lab.py init`；答案文件保持不变。使用 `conda deactivate` 退出环境。
