# AI Contract Review System

智能合同审查系统，基于 LangChain + LangGraph 构建的 AI Agent。

## 功能特性

- 📄 支持多种文档格式：PDF、Word、TXT
- 🔍 智能合规性检查
- ⚠️ 风险识别与评估
- 📊 结构化审查报告
- 🔧 可配置审查规则
- 🤖 支持多种 LLM：OpenAI、Azure OpenAI、Ollama

## 快速开始

### 1. 安装依赖

```bash
pip install -r requirements.txt
```

### 2. 配置环境变量

```bash
cp .env.example .env
# 编辑 .env 文件，配置你的 API 密钥
```

### 3. 启动服务

```bash
uvicorn main:app --reload
```

### 4. 使用 API

- 健康检查：`GET http://localhost:8000/health`
- 合同分析：`POST http://localhost:8000/analyze`（上传文件）

## 项目结构

```
ai-contract-review/
├── main.py              # FastAPI 入口
├── config.py            # 配置管理
├── requirements.txt     # 依赖列表
├── agent/              # AI Agent 逻辑
│   └── contract_agent.py
├── tools/              # 工具函数
│   ├── document_parser.py
│   ├── compliance_checker.py
│   └── llm_client.py
└── rules/              # 审查规则
    └── review_rules.yaml
```

## API 响应格式

```json
{
  "summary": "合同摘要...",
  "risks": [
    {
      "clause": "第5条",
      "issue": "解约权不对等",
      "severity": "high"
    }
  ],
  "compliance": ["签署方完整", "缺少争议解决条款"],
  "score": 6
}
```