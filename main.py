"""
微信公众号 Webhook 服务入口
使用 FastAPI + wechatpy 处理微信消息
"""
from __future__ import annotations

import hashlib
import logging
import time
import xml.etree.ElementTree as ET

import uvicorn
from fastapi import FastAPI, Query, Request, Response
from fastapi.responses import PlainTextResponse

import config
from bot.agent import chat, clear_session

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s - %(message)s",
)
logger = logging.getLogger(__name__)

app = FastAPI(title="电商客服机器人", version="1.0.0")


# ---------- 微信签名验证 ----------

def _check_signature(token: str, timestamp: str, nonce: str, signature: str) -> bool:
    """验证微信服务器签名"""
    parts = sorted([token, timestamp, nonce])
    sha1 = hashlib.sha1("".join(parts).encode("utf-8")).hexdigest()
    return sha1 == signature


# ---------- 微信消息解析 / 构造 ----------

def _parse_message(xml_body: bytes) -> dict:
    """解析微信 XML 消息"""
    root = ET.fromstring(xml_body)
    return {child.tag: (child.text or "") for child in root}


def _build_text_reply(to_user: str, from_user: str, content: str) -> str:
    """构造文本回复 XML"""
    timestamp = int(time.time())
    return f"""<xml>
  <ToUserName><![CDATA[{to_user}]]></ToUserName>
  <FromUserName><![CDATA[{from_user}]]></FromUserName>
  <CreateTime>{timestamp}</CreateTime>
  <MsgType><![CDATA[text]]></MsgType>
  <Content><![CDATA[{content}]]></Content>
</xml>"""


# ---------- 路由 ----------

@app.get("/wechat", summary="微信服务器验证")
async def wechat_verify(
    signature: str = Query(...),
    timestamp: str = Query(...),
    nonce: str = Query(...),
    echostr: str = Query(...),
) -> PlainTextResponse:
    """微信公众号接入验证"""
    if _check_signature(config.WECHAT_TOKEN, timestamp, nonce, signature):
        return PlainTextResponse(echostr)
    return PlainTextResponse("Invalid signature", status_code=403)


@app.post("/wechat", summary="接收微信消息")
async def wechat_handler(
    request: Request,
    signature: str = Query(...),
    timestamp: str = Query(...),
    nonce: str = Query(...),
) -> Response:
    """接收并处理微信用户消息"""
    # 1. 验证签名
    if not _check_signature(config.WECHAT_TOKEN, timestamp, nonce, signature):
        return PlainTextResponse("Invalid signature", status_code=403)

    # 2. 解析消息
    body = await request.body()
    msg = _parse_message(body)
    logger.info("Received message: %s", msg)

    msg_type = msg.get("MsgType", "")
    from_user = msg.get("FromUserName", "")
    to_user = msg.get("ToUserName", "")

    # 3. 只处理文本消息
    if msg_type != "text":
        content = "您好！目前我只支持文字咨询，请发送文字消息 😊"
        return Response(
            content=_build_text_reply(from_user, to_user, content),
            media_type="application/xml",
        )

    user_text = msg.get("Content", "").strip()

    # 4. 处理特殊指令
    if user_text in ("清除记录", "重新开始", "reset"):
        await clear_session(from_user)
        content = "✅ 会话已重置，很高兴再次为您服务！请问有什么可以帮您？"
        return Response(
            content=_build_text_reply(from_user, to_user, content),
            media_type="application/xml",
        )

    # 5. 调用 AI 客服
    try:
        reply_text = await chat(user_id=from_user, user_message=user_text)
    except Exception as e:
        logger.exception("Chat error for user %s: %s", from_user, e)
        reply_text = "系统繁忙，请稍后再试，或拨打客服热线 400-xxx-xxxx"

    return Response(
        content=_build_text_reply(from_user, to_user, reply_text),
        media_type="application/xml",
    )


@app.get("/health", summary="健康检查")
async def health_check() -> dict:
    return {"status": "ok", "service": "ecommerce-wechat-bot"}


# ---------- 开发模式入口 ----------

if __name__ == "__main__":
    uvicorn.run(
        "main:app",
        host=config.HOST,
        port=config.PORT,
        reload=True,
        log_level="info",
    )
