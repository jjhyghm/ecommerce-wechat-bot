"""
OpenAI Agent 核心：多轮对话 + Function Calling
"""
from __future__ import annotations

import json
import logging
from typing import Any

import redis.asyncio as aioredis
from openai import AsyncOpenAI

import config
from bot.handlers import TOOL_DISPATCH, TOOLS

logger = logging.getLogger(__name__)

# Redis 客户端（会话存储）
_redis: aioredis.Redis | None = None


async def get_redis() -> aioredis.Redis:
    global _redis
    if _redis is None:
        _redis = await aioredis.from_url(config.REDIS_URL, decode_responses=True)
    return _redis


# OpenAI 客户端
openai_client = AsyncOpenAI(api_key=config.OPENAI_API_KEY)

SESSION_TTL = 1800  # 30分钟会话保留


async def get_session(user_id: str) -> list[dict]:
    """从 Redis 读取用户历史消息"""
    r = await get_redis()
    key = f"session:{user_id}"
    data = await r.get(key)
    if data:
        return json.loads(data)
    return []


async def save_session(user_id: str, messages: list[dict]) -> None:
    """保存会话到 Redis"""
    r = await get_redis()
    key = f"session:{user_id}"
    # 只保留最近 20 条消息，避免 token 超限
    messages = messages[-20:]
    await r.set(key, json.dumps(messages, ensure_ascii=False), ex=SESSION_TTL)


async def clear_session(user_id: str) -> None:
    """清除用户会话"""
    r = await get_redis()
    await r.delete(f"session:{user_id}")


def _call_tool(name: str, arguments: str) -> Any:
    """执行工具函数"""
    func = TOOL_DISPATCH.get(name)
    if not func:
        return {"error": f"未知工具: {name}"}
    try:
        args = json.loads(arguments)
        return func(**args)
    except Exception as e:
        logger.exception("Tool %s error: %s", name, e)
        return {"error": str(e)}


async def chat(user_id: str, user_message: str) -> str:
    """
    多轮对话入口
    :param user_id:      微信 openid
    :param user_message: 用户输入文本
    :return:             机器人回复文本
    """
    # 1. 加载历史会话
    messages = await get_session(user_id)

    # 2. 初始化系统提示（首轮）
    if not messages:
        messages = [{"role": "system", "content": config.SYSTEM_PROMPT}]

    # 3. 追加用户消息
    messages.append({"role": "user", "content": user_message})

    # 4. 循环调用 OpenAI（支持多步 Function Calling）
    max_rounds = 5
    for _ in range(max_rounds):
        response = await openai_client.chat.completions.create(
            model=config.OPENAI_MODEL,
            messages=messages,
            tools=TOOLS,
            tool_choice="auto",
        )

        choice = response.choices[0]
        msg = choice.message

        # 追加 assistant 消息（含 tool_calls 或纯文本）
        messages.append(msg.model_dump(exclude_none=True))

        if choice.finish_reason == "tool_calls":
            # 执行所有工具调用
            for tc in msg.tool_calls:
                result = _call_tool(tc.function.name, tc.function.arguments)
                logger.info("Tool %s result: %s", tc.function.name, result)
                messages.append(
                    {
                        "role": "tool",
                        "tool_call_id": tc.id,
                        "content": json.dumps(result, ensure_ascii=False),
                    }
                )
            # 继续循环，让模型生成最终回复
            continue

        # finish_reason == "stop"：得到最终回复
        reply = msg.content or "抱歉，我暂时无法处理您的请求，请稍后再试。"
        break
    else:
        reply = "处理超时，请联系人工客服。"

    # 5. 保存会话
    await save_session(user_id, messages)

    return reply
