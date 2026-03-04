
请严格按照以下 5 个步骤操作：

### 第一步：下载并安装 Docker Desktop

这是运行环境的基础。

1. **下载**：访问 Docker 官网下载 Windows 版：
* 链接：[Docker Desktop for Windows](https://www.docker.com/products/docker-desktop/)


2. **安装**：
* 双击安装包，所有选项保持默认，一路点击 "Next" 直到完成。
* 安装完成后，**重启电脑**（这一步很重要，因为需要配置虚拟化环境）。


3. **启动**：
* 电脑重启后，打开 "Docker Desktop" 应用。
* 如果是第一次运行，它可能会让你同意服务条款，点击 Accept。
* **确认状态**：看到 Docker Desktop 左下角的鲸鱼图标变成**绿色**（或者显示 "Engine running"），说明 Docker 已经准备好了。



---

### 第二步：创建项目配置文件 (`docker-compose.yml`)

我们需要一个文件来告诉 Docker：“请帮我启动一个装好 pgvector 插件的 PostgreSQL 数据库”。

1. 打开你的代码编辑器（VS Code）。
2. 在你的**项目根目录**（也就是 `ai-interview-platform` 文件夹下），创建一个新文件，命名为 `docker-compose.yml`。
3. **复制并粘贴**以下全部代码到该文件中：

```yaml
version: '3.8'

services:
  db:
    # 使用预装了 pgvector 插件的官方镜像
    # 这样你就不用自己去编译安装插件了，非常方便
    image: pgvector/pgvector:pg16
    container_name: interview_db
    restart: always
    
    # 数据库的账号密码配置
    environment:
      POSTGRES_USER: postgres
      POSTGRES_PASSWORD: mysecretpassword  # 这里的密码可以自己改，记得代码里也要对应修改
      POSTGRES_DB: ai_interview_db         # 容器启动时会自动创建这个数据库
      
    # 端口映射：把容器里的 5432 端口暴露给你的电脑
    ports:
      - "5432:5432"
      
    # 数据卷挂载
    volumes:
      # 1. 确保数据持久化，即使删了容器数据还在
      - postgres_data:/var/lib/postgresql/data
      # 2. 自动执行初始化脚本（开启 vector 插件）
      - ./init_db:/docker-entrypoint-initdb.d

volumes:
  postgres_data:

```

---

### 第三步：创建初始化脚本 (`init.sql`)

我们需要告诉数据库，启动后第一时间把“向量插件”打开，否则后面无法存储向量数据。

1. 在项目根目录下，创建一个新的**文件夹**，命名为 `init_db`。
2. 在 `init_db` 文件夹里，创建一个新文件，命名为 `init.sql`。
3. **复制并粘贴**以下代码到该文件中：

```sql
-- 开启 pgvector 扩展
-- 这是根据你的《数据库详细介绍.md》文档要求的关键步骤
CREATE EXTENSION IF NOT EXISTS vector;

```

**现在的目录结构应该是这样的：**

```
ai-interview-platform/
├── docker-compose.yml      (刚创建的)
├── init_db/                (刚创建的文件夹)
│   └── init.sql            (刚创建的文件)
├── backend/
├── frontend/
└── ...

```

---

### 第四步：一键启动数据库

万事俱备，现在让它跑起来。

1. 在 VS Code 中，点击顶部菜单栏的 **“终端 (Terminal)”** -> **“新建终端 (New Terminal)”**。
2. 确保终端路径是在 `ai-interview-platform` 根目录下。
3. 输入以下命令并回车：

```bash
docker compose up -d

```

* Docker 会开始下载镜像（第一次可能需要几分钟，取决于网速）。
* 下载完成后，它会自动启动数据库。
* 当看到 `Started` 或 `Running` 字样时，说明成功了。

---

### 第五步：验证是否成功

我们要确认数据库真的装好了，并且插件也开启了。

1. 在终端输入以下命令：
```bash
docker ps

```


2. **查看结果**：
* 你应该能看到一行记录，NAMES 列显示 `interview_db`，STATUS 显示 `Up ...`。


3. **进入数据库检查插件**（可选，确认用）：
输入以下命令直接进入数据库内部：
```bash
docker exec -it interview_db psql -U postgres -d ai_interview_db

```


进入后，输入 `\dx` 并回车。
* 如果看到列表中有 `vector`，说明 **pgvector 插件安装成功！**
* 输入 `\q` 退出。



---

### 后续操作提醒

数据库现在已经准备好了，连接信息如下（写代码时要用）：

* **主机 (Host)**: `localhost`
* **端口 (Port)**: `5432`
* **数据库名 (Database)**: `ai_interview_db`
* **用户名 (User)**: `postgres`
* **密码 (Password)**: `mysecretpassword` (或者你在 docker-compose.yml 里改的那个)

接下来你就可以去配置 Flask 的 `config.py` 并运行 `flask db upgrade` 来生成表结构了。