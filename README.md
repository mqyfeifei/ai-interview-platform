# AI模拟面试与能力提升软件 - 项目完整搭建指南

## 一、项目概述

这是一个基于 **Vue.js + Flask** 的前后端分离项目，旨在实现AI模拟面试及能力评估的核心功能。本项目集成了本地AI模型与向量数据库，支持智能化对话与面试分析。

## 技术选型与开发环境

| **模块** | **技术选型**                                                 |
| -------- | ------------------------------------------------------------ |
| 前端     | 编辑器：VS Code<br>框架：Vue 3、Vue Router、Vuex<br>网络请求：Axios |
| 后端     | 编辑器：PyCharm / VS Code<br>语言：Python 3.12.3<br>框架：Flask<br>ORM：SQLAlchemy<br>跨域：Flask-CORS |
| 数据库   | 容器化部署：Docker Desktop<br>数据库引擎：PostgreSQL 16 (集成 pgvector 插件)<br>可视化工具：Navicat |

------

## 二、完整的项目结构

```text
ai-interview-platform/
├── frontend/                    # Vue前端项目
│   ├── public/                  # 静态资源
│   ├── src/                     # 源代码 (api, assets, components, views, router, store, utils)
│   ├── package.json             # 前端依赖配置
│   └── vue.config.js            # Vue配置
├── backend/                     # Flask后端项目
│   ├── app/                     # 应用工厂与核心逻辑 (models, api, services, utils)
│   ├── requirements.txt         # 后端依赖包
│   ├── run.py                   # 后端启动入口
│   └── data_create_and_import.py# 数据初始化脚本
├── docker-compose.yml           # Docker数据库服务配置
├── init_db/                     # 数据库初始化脚本目录
│   └── init.sql                 # pgvector 插件开启脚本
└── README.md                    # 项目说明文档
```

---

## 三、获取项目

请打开终端 (Terminal / CMD / PowerShell 均可)，将项目代码克隆到本地并进入目录：

```cmd
git clone <该项目GitHub/GitLab仓库地址>
cd ai-interview-platform
```

------

## 四、前端环境准备与运行

## 1. 安装基础工具

- **Node.js 和 npm**：访问 [Node.js 官网](https://nodejs.org/) 下载长期支持版（LTS），安装时勾选“Add to PATH”。安装后在终端运行 `node -v` 和 `npm -v` 验证。

- **Vue CLI**（如未安装，请在终端执行以下命令）：

  ```cmd
  npm install -g @vue/cli
  # 如果已安装旧版本可更新：npm update -g @vue/cli
  ```

## 2. 安装依赖并启动前端

在终端中进入前端目录并运行：

```cmd
cd frontend
# 安装依赖
npm install
# 运行前端开发服务器
npm run serve
```

------

## 五、数据库部署 (Docker)

本项目使用 Docker 部署自带 `pgvector` 向量插件的 PostgreSQL 数据库。

## 1. 安装 Docker Desktop

访问 [Docker 官网](https://www.docker.com/products/docker-desktop/) 下载 Windows/Mac 版本并安装。安装完成后**务必重启电脑**。打开 Docker Desktop，确保左下角显示绿色引擎图标（Engine running）。

## 2. 一键启动数据库容器

在项目根目录（`ai-interview-platform`）下，确保包含 `docker-compose.yml` 和 `init_db` 目录，然后打开终端执行：

```cmd
docker compose up -d
```

*Docker 将自动拉取镜像并启动包含 pgvector 的数据库容器。*

## 3. 验证数据库状态

- 在终端执行 `docker ps`，若看到名为 `interview_db` 的容器且状态为 `Up`，即启动成功。
- **数据库连接信息（开发配置使用）**：
  - **主机 (Host)**: `localhost`
  - **端口 (Port)**: `5432`
  - **数据库名 (Database)**: `ai_interview_db`
  - **用户名 (User)**: `postgres`
  - **密码 (Password)**: `mysecretpassword`

------

## 六、后端环境部署与初始化

## 1. 创建虚拟环境与安装依赖

打开终端，进入 `backend` 目录并配置环境：

```cmd
cd backend

# 创建虚拟环境 (推荐使用 Python 3.12.3)
python -m venv venv

# 激活虚拟环境 (Windows CMD 或 PowerShell):
venv\Scripts\activate
# 激活虚拟环境 (macOS/Linux/Git ):
# source venv/bin/activate

# 安装数据库驱动、迁移工具及其他项目依赖
pip install psycopg2-binary flask-migrate pgvector
# 建议一并安装全部依赖：
pip install -r requirements.txt
```

## 2. 数据库表结构初始化 (迁移三部曲)

**⚠️ 重要提醒：如果你的数据库表结构发生了改变需要重新初始化迁移环境，在执行 `flask db init` 之前，必须进行以下步骤：**

**正确的彻底重置步骤（两者必须同进同退）：**

1. **清本地**：手动删除 `backend` 目录下的 `migrations` 文件夹（如果存在）。
2. **清数据库记录**：使用 Navicat 或数据库工具连接到你的 PostgreSQL 数据库，找到并**删除 `alembic_version` 表**（执行 SQL: `DROP TABLE alembic_version;`）。若不再需要旧测试数据，也可直接清空整个数据库。
3. **重新初始化**：完成上述两步同步清理后，再继续执行下方的初始化命令。

> 否则可能出现初始化冲突或引发 `Error: Can't locate revision identified by 'xxxx'` 的致命报错。

首先需要告诉系统 Flask 的启动入口在哪里，然后再执行数据库的迁移操作。请**根据你当前使用的终端类型**，运行对应的命令：

**👉 如果你使用的是 Windows CMD (命令提示符)：**

```cmd
# 1. 设置环境变量
set FLASK_APP=run.py

# 2. 初始化迁移仓库（项目生命周期仅执行一次）
flask db init

# 3. 生成迁移脚本
flask db migrate -m "init db"

# 4. 将表结构应用到数据库
flask db upgrade
```

**👉 如果你使用的是 Windows PowerShell：**

```cmd
# 1. 设置环境变量
$env:FLASK_APP="run.py"

# 2. 初始化迁移仓库
flask db init

# 3. 生成迁移脚本
flask db migrate -m "init db"

# 4. 将表结构应用到数据库
flask db upgrade
```

**👉 如果你使用的是 macOS / Linux / Git ：**

```bash
# 1. 设置环境变量
export FLASK_APP=run.py

# 2. 初始化迁移仓库
flask db init

# 3. 生成迁移脚本
flask db migrate -m "init db"

# 4. 将表结构应用到数据库
flask db upgrade
```

## 3. 初始化知识库与配置

确保 Docker 数据库正在运行，在 `backend` 的虚拟环境终端中执行脚本以初始化表数据：

```cmd
python data_create_and_import.py
```

**⚠️ 重要：本地大模型向量维度修正与字段补全**

由于嵌入了本地模型，请打开 Navicat 或使用 `psql` 连接数据库，执行以下 SQL 语句来修改向量维度（改为 512）、更新提示词并补充缺失字段：

```sql
-- 1. 修改向量维度为 512（需先清空数据防冲突）
TRUNCATE TABLE questions CASCADE;
TRUNCATE TABLE knowledge_items CASCADE;
TRUNCATE TABLE resources CASCADE;

ALTER TABLE questions ALTER COLUMN embedding TYPE vector(512);
ALTER TABLE knowledge_items ALTER COLUMN embedding TYPE vector(512);
ALTER TABLE resources ALTER COLUMN embedding TYPE vector(512);

-- 2. 补全面试评估相关缺失字段
ALTER TABLE interviews ADD COLUMN evaluation_highlights TEXT;
ALTER TABLE interviews ADD COLUMN evaluation_improvements TEXT;
ALTER TABLE interviews ADD COLUMN evaluation_suggestions TEXT;

-- 3. 更新系统提示词（强制 AI 输出结束标记）
UPDATE ai_prompts 
SET system_prompt = system_prompt || '
【核心指令】：题量请结合知识库规模动态控制（建议8-16题），达到充分评估后再结束。结束时最后一句必须感谢候选人，并在该句末尾加上特殊标记 [INTERVIEW_OVER]。'
WHERE is_active = true;
```

## 5. 启动后端服务

一切就绪后，在虚拟环境终端中启动 Flask 后端：

```cmd
flask run
# 或者使用 Python 直接运行
python run.py
```
