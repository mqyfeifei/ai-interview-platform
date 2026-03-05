## A.初始化数据库
#### 1. 确保在正确的目录下

打开终端，确保你所在的路径是 `backend` 文件夹（能看到 `run.py` 的那个目录）。

```bash
cd backend

```

#### 2. 安装必要的依赖库

Flask 连接 PostgreSQL 需要专门的驱动库，你的虚拟环境可能还没装。

```bash
# 激活你的虚拟环境 (Windows)
venv\Scripts\activate

# 安装数据库驱动和迁移工具
pip install psycopg2-binary flask-migrate pgvector

```

#### 3. 设置 Flask 环境变量 (告诉 Flask 启动入口在哪里)

Flask 需要知道哪个文件是你的 APP 入口（通常是 `run.py`）。

* **Windows CMD**:
```cmd
set FLASK_APP=run.py

```



#### 4. 执行初始化命令 (三部曲)

**第一步：初始化迁移仓库 (Init)**

* **命令**：`flask db init`
* **作用**：这会在 `backend` 目录下创建一个名为 `migrations` 的文件夹。
* **注意**：这个命令在项目生命周期里**只运行一次**。

**第二步：生成迁移脚本 (Migrate)**

* **命令**：`flask db migrate -m "init db"`
* **作用**：Flask 会扫描你的 `models` 代码，对比数据库现状，生成一个 SQL 变更脚本（放在 `migrations/versions` 里）。
* **成功标志**：终端提示 `Detected change... Generated ...`。

**第三步：应用到数据库 (Upgrade)**

* **命令**：`flask db upgrade`
* **作用**：真正去执行 SQL，在 Docker 里的数据库创建表。
* **成功标志**：没有报错，直接返回命令行。

---

### 如何验证成功？

执行完 `flask db upgrade` 后，你可以用 Navicat 连接数据库，或者直接看 Docker：

1. 查看 Docker 日志：
```bash
docker logs interview_db

```


(你应该能看到一些连接成功的日志)
2. 如果这三步都报错，通常是因为：
* **密码错了**：检查 `config.py` 里的密码和 `docker-compose.yml` 是否一致。
* **数据库没启动**：运行 `docker ps` 看看容器是不是在运行。
* **没装库**：忘记 `pip install psycopg2-binary`。



## B.初始化表
确保 Docker 容器正在运行（特别是数据库容器）。
进入后端环境（如果你是在本地开发环境）

```Bash
# 假设你在 backend 目录下，且已激活虚拟环境
python init_data.py
```
或者在 Docker 容器内运行（如果后端也是容器化的）：

```Bash
# 进入后端容器
docker exec -it <后端容器ID> /bin/bash
# 执行脚本
python init_data.py
```



## C.由于嵌入了本地模型，请检查向量维度，维度不正确进数据库修改
```Bash
-- 清空表数据（防范维度冲突报错）
TRUNCATE TABLE questions CASCADE;
TRUNCATE TABLE knowledge_items CASCADE;

-- 修改向量维度为 512
ALTER TABLE questions ALTER COLUMN embedding TYPE vector(512);
ALTER TABLE knowledge_items ALTER COLUMN embedding TYPE vector(512);

-- 清空 resources 表数据（防范维度冲突报错）
TRUNCATE TABLE resources CASCADE;

-- 修改向量维度为 512
ALTER TABLE resources ALTER COLUMN embedding TYPE vector(512);
```


提示词修改，如果数据库里面提示词没有结束语，请执行以下sql语句
```Bash
UPDATE ai_prompts 
SET system_prompt = system_prompt || '
【核心指令】：当你觉得已经问了足够多的问题（例如超过5题），或者你认为已经充分评估了该候选人的能力时，请主动结束面试。结束时，请务必在你的回复文本的最后面加上特殊标记 [INTERVIEW_OVER]。'
WHERE is_active = true;
```
检查interview是否具有以下三个字段，没有执行以下sql语句
```Bash
ALTER TABLE interviews ADD COLUMN evaluation_highlights TEXT;
ALTER TABLE interviews ADD COLUMN evaluation_improvements TEXT;
ALTER TABLE interviews ADD COLUMN evaluation_suggestions TEXT;
```

## D.初始化知识库
运行`backend/import_kb.py`来导入数据库里面知识内容
