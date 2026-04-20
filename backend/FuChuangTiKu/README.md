# FuChuangTiKu - 综合研发与工程岗位知识库

本目录沉淀 **后端 / 前端 / 计算机视觉 / 网络工程 / 测试开发** 五大岗位题库与知识点数据，供管理端批量导入与面试端动态选题使用。

## 当前数据结构

- `kb.config.yaml`：全局配置（字段定义、状态流转、岗位映射）
- `index.yaml`：导入索引（管理员“批量导入”会读取 datasets.path）
- `data/questions/`：题目库（`technical / project_deep_dive / scenario_design / behavioral`）
- `data/examples/`：优秀回答范例
- `data/knowledge_points/`：知识点地图

## 企业专用题库支持（已启用）

questions 文件中的 `source` 现已支持：

1. 通用来源（如 `Nowcoder`、`Tech_Blog`、`Interview_Bank`）
2. 企业来源（如 `字节跳动`、`阿里巴巴`、`腾讯`、`华为`、`美团` 等）

系统会结合会话中的 `target_source` 做来源过滤：优先企业来源题，再回落到“通用”题，避免题源跑偏。

## 管理端导入约定

1. 批量导入入口：`/api/v1/admin/questions/import`
2. 未上传文件时，后端按 `index.yaml -> datasets -> path` 自动扫描
3. `index.yaml` 中 path 必须是以 `FuChuangTiKu/` 为根的相对路径，例如：
   - `data/questions/backend_technical_interview_questions.yaml`
   - `data/questions/cv_scenario_design_questions.yaml`

## 维护建议

1. 题目 `id` 保持全局唯一（建议按岗位前缀）
2. 新增企业来源时，同步更新对应 questions 文件头部 `source` 列表
3. 调整题库结构后，同步更新 `index.yaml` 与本 README
