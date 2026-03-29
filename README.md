# 电商客服机器人 — Python + OpenAI + 微信公众号

> 基于 OpenAI GPT 的智能电商客服机器人，接入微信公众号，支持订单查询、退货申请、商品推荐。

## 功能特性

| 能力 | 说明 |
|------|------|
| 🔍 订单查询 | 输入订单号或手机号，实时查询状态与物流 |
| 🔄 退货退款 | 引导用户发起退货，自动生成退货单号 |
| 🛍️ 商品推荐 | 根据关键词、类别、预算智能推荐商品 |
| 💬 多轮对话 | 基于 Redis 的会话记忆，支持上下文连续对话 |
| 🤖 Function Calling | OpenAI Tools 自动决策调用哪个业务接口 |

## 项目结构

```
ecommerce-wechat-bot/
├── main.py              # FastAPI 服务入口 & 微信 Webhook
├── config.py            # 配置加载（环境变量）
├── requirements.txt     # 依赖列表
├── .env.example         # 环境变量示例
└── bot/
    ├── __init__.py
    ├── agent.py         # OpenAI 多轮对话 + Function Calling
    └── handlers.py      # 业务工具函数 & OpenAI Tools Schema
```

## 快速开始

### 1. 安装依赖

```bash
pip install -r requirements.txt
```

### 2. 配置环境变量

```bash
cp .env.example .env
# 编辑 .env，填入 OpenAI API Key 和微信公众号配置
```

### 3. 启动 Redis

```bash
docker run -d -p 6379:6379 redis:alpine
```

### 4. 启动服务

```bash
python main.py
# 或生产模式
uvicorn main:app --host 0.0.0.0 --port 8000
```

### 5. 配置微信公众号

1. 登录 [微信公众平台](https://mp.weixin.qq.com/)
2. 进入「设置与开发 → 基本配置」
3. 填写服务器配置：
   - **URL**：`https://your-domain.com/wechat`（需 HTTPS，可用 [ngrok](https://ngrok.com) 内网穿透测试）
   - **Token**：与 `.env` 中 `WECHAT_TOKEN` 一致
   - **消息加密方式**：选「明文模式」（开发阶段）
4. 点击「提交」验证通过即接入成功

## 对话示例

```
用户：我想查一下我的订单
机器人：您好！请提供您的订单号，我来帮您查询 😊

用户：订单号是 2024001
机器人：为您查询到订单信息：
  📦 商品：无线蓝牙耳机 Pro
  📊 状态：已发货
  🚚 物流：顺丰快递 SF1234567890
  📅 预计到达：2024-12-20

用户：我想退货
机器人：好的，请告诉我退货原因，我来为您发起申请...

用户：推荐一款300块以内的耳机
机器人：为您推荐以下商品：
  1. 无线蓝牙耳机 Pro - ¥299
     40小时续航，主动降噪，评分 4.8 ⭐
  ...
```

## 架构说明

```
微信用户
  │ 发送消息
  ▼
微信公众号服务器
  │ POST /wechat
  ▼
FastAPI (main.py)          ← 验证签名、解析 XML
  │
  ▼
bot/agent.py               ← 多轮对话管理
  ├── Redis                ← 会话历史存储（30分钟TTL）
  └── OpenAI Chat API      ← GPT 理解意图 + Function Calling
        │ tool_calls
        ▼
      bot/handlers.py      ← 查订单 / 退货 / 推荐商品
        │ 返回结果 JSON
        ▼
      OpenAI 生成自然语言回复
        │
        ▼
      微信用户收到回复
```

## 接入真实数据库

`bot/handlers.py` 中的函数目前使用 Mock 数据。替换为真实数据库只需修改对应函数：

```python
# 示例：接入 MySQL 订单查询
async def query_order(order_id: str, phone=None):
    async with db.connect() as conn:
        row = await conn.fetchone(
            "SELECT * FROM orders WHERE order_id = %s", order_id
        )
    return {"success": bool(row), "order": dict(row) if row else None}
```

## 生产部署建议

- 使用 `gunicorn + uvicorn workers` 多进程部署
- 配置 Nginx 反向代理 + SSL 证书（微信要求 HTTPS）
- Redis Sentinel 或 Redis Cluster 保障会话可用性
- 接入企业真实订单系统、ERP 替换 Mock 数据

## License

MIT
