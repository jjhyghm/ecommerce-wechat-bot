import os
from dotenv import load_dotenv

load_dotenv()

# OpenAI
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "")
OPENAI_MODEL = os.getenv("OPENAI_MODEL", "gpt-4o-mini")

# WeChat Official Account
WECHAT_TOKEN = os.getenv("WECHAT_TOKEN", "your_wechat_token")
WECHAT_APP_ID = os.getenv("WECHAT_APP_ID", "")
WECHAT_APP_SECRET = os.getenv("WECHAT_APP_SECRET", "")
WECHAT_ENCODING_AES_KEY = os.getenv("WECHAT_ENCODING_AES_KEY", "")

# Server
HOST = os.getenv("HOST", "0.0.0.0")
PORT = int(os.getenv("PORT", 8000))

# Redis (for session storage)
REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379/0")

# System prompt for the AI agent
SYSTEM_PROMPT = """你是一名专业的电商客服助理，代表本店为用户提供热情、专业的服务。

你的能力包括：
1. **订单查询**：根据用户提供的订单号或手机号，查询订单状态、物流信息
2. **退货退款**：指导用户发起退货申请，说明退货流程和政策
3. **商品推荐**：根据用户需求、喜好和预算，推荐合适的商品

回复规范：
- 语气友好、耐心，使用"您"称呼用户
- 回复简洁明了，避免冗长
- 若需要订单号等信息，主动引导用户提供
- 无法处理的问题，告知转接人工客服

退货政策：
- 7天无理由退货（非人为损坏）
- 退货需保持商品及包装完好
- 退款3-5个工作日到账
"""
