"""
业务处理器：订单查询、退货申请、商品推荐
实际项目中应替换为真实数据库/API调用
"""
from __future__ import annotations
import random
from typing import Optional


# ---------- Mock 数据 ----------

MOCK_ORDERS = {
    "2024001": {
        "order_id": "2024001",
        "product": "无线蓝牙耳机 Pro",
        "status": "已发货",
        "logistics": "顺丰快递 SF1234567890",
        "estimated_delivery": "2024-12-20",
        "amount": 299.00,
        "create_time": "2024-12-15 10:30:00",
    },
    "2024002": {
        "order_id": "2024002",
        "product": "智能手表 SE",
        "status": "待发货",
        "logistics": "暂无物流信息",
        "estimated_delivery": "2024-12-22",
        "amount": 599.00,
        "create_time": "2024-12-17 14:20:00",
    },
    "2024003": {
        "order_id": "2024003",
        "product": "便携充电宝 20000mAh",
        "status": "已完成",
        "logistics": "顺丰快递 SF9876543210（已签收）",
        "estimated_delivery": "2024-12-10",
        "amount": 129.00,
        "create_time": "2024-12-05 09:00:00",
    },
}

MOCK_PRODUCTS = [
    {
        "id": "P001",
        "name": "无线蓝牙耳机 Pro",
        "price": 299.0,
        "category": "耳机",
        "rating": 4.8,
        "tags": ["音质好", "降噪", "续航长"],
        "description": "40小时超长续航，主动降噪，Hi-Res认证",
    },
    {
        "id": "P002",
        "name": "智能手表 SE",
        "price": 599.0,
        "category": "手表",
        "rating": 4.7,
        "tags": ["健康监测", "防水", "多功能"],
        "description": "血氧心率监测，50米防水，14天续航",
    },
    {
        "id": "P003",
        "name": "便携充电宝 20000mAh",
        "price": 129.0,
        "category": "充电",
        "rating": 4.9,
        "tags": ["大容量", "快充", "轻薄"],
        "description": "20000mAh大容量，65W超级快充，仅重280g",
    },
    {
        "id": "P004",
        "name": "机械键盘 TKL",
        "price": 399.0,
        "category": "键盘",
        "rating": 4.6,
        "tags": ["手感好", "RGB背光", "耐用"],
        "description": "Cherry轴体，全键无冲，RGB背光",
    },
    {
        "id": "P005",
        "name": "4K 网络摄像头",
        "price": 499.0,
        "category": "摄像头",
        "rating": 4.7,
        "tags": ["高清", "自动对焦", "降噪麦克风"],
        "description": "4K超清，AI自动对焦，内置降噪双麦克风",
    },
    {
        "id": "P006",
        "name": "人体工学鼠标",
        "price": 229.0,
        "category": "鼠标",
        "rating": 4.8,
        "tags": ["舒适", "无线", "精准"],
        "description": "垂直握姿设计，缓解手腕疲劳，2.4G无线",
    },
]

RETURN_POLICY = {
    "days": 7,
    "conditions": [
        "商品未使用，保持原包装完好",
        "非人为损坏（如跌落、进水等不在范围内）",
        "配件（说明书、保修卡等）需齐全",
    ],
    "steps": [
        "1. 联系客服申请退货，提供订单号",
        "2. 客服审核通过后，系统发送退货地址",
        "3. 将商品寄回（建议使用顺丰，留存单号）",
        "4. 仓库收货验货（1-2个工作日）",
        "5. 退款原路返回（3-5个工作日到账）",
    ],
    "address": "上海市徐汇区田林路xxx号xx楼 收货人：退货中心 电话：400-xxx-xxxx",
}


# ---------- 工具函数（供 OpenAI Function Calling 使用）----------

def query_order(order_id: str, phone: Optional[str] = None) -> dict:
    """查询订单信息"""
    order = MOCK_ORDERS.get(order_id.strip())
    if order:
        return {"success": True, "order": order}
    # 模拟按手机号查询
    if phone:
        sample = random.choice(list(MOCK_ORDERS.values()))
        return {"success": True, "order": sample, "note": "已找到您名下最近订单"}
    return {"success": False, "message": f"未找到订单号 {order_id}，请确认后重试"}


def initiate_return(order_id: str, reason: str) -> dict:
    """发起退货申请"""
    order = MOCK_ORDERS.get(order_id.strip())
    if not order:
        return {"success": False, "message": f"未找到订单 {order_id}"}
    if order["status"] not in ("已完成", "已发货"):
        return {
            "success": False,
            "message": f"订单状态为「{order['status']}」，暂不支持退货",
        }
    return {
        "success": True,
        "return_no": f"RT{order_id}{random.randint(1000,9999)}",
        "message": "退货申请已提交，请将商品寄至以下地址",
        "policy": RETURN_POLICY,
    }


def get_return_policy() -> dict:
    """获取退货政策"""
    return {"success": True, "policy": RETURN_POLICY}


def recommend_products(
    keyword: Optional[str] = None,
    category: Optional[str] = None,
    max_price: Optional[float] = None,
    top_n: int = 3,
) -> dict:
    """推荐商品"""
    results = list(MOCK_PRODUCTS)

    if category:
        results = [p for p in results if category.lower() in p["category"].lower()]

    if keyword:
        kw = keyword.lower()
        results = [
            p
            for p in results
            if kw in p["name"].lower()
            or kw in p["description"].lower()
            or any(kw in t for t in p["tags"])
        ]

    if max_price is not None:
        results = [p for p in results if p["price"] <= max_price]

    # 按评分降序
    results.sort(key=lambda p: p["rating"], reverse=True)

    return {
        "success": True,
        "products": results[:top_n],
        "total": len(results),
    }


# ---------- OpenAI Tools Schema ----------

TOOLS = [
    {
        "type": "function",
        "function": {
            "name": "query_order",
            "description": "根据订单号或手机号查询订单状态和物流信息",
            "parameters": {
                "type": "object",
                "properties": {
                    "order_id": {
                        "type": "string",
                        "description": "订单号，例如 2024001",
                    },
                    "phone": {
                        "type": "string",
                        "description": "用户手机号（可选，用于辅助查询）",
                    },
                },
                "required": ["order_id"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "initiate_return",
            "description": "为用户发起退货退款申请",
            "parameters": {
                "type": "object",
                "properties": {
                    "order_id": {
                        "type": "string",
                        "description": "需要退货的订单号",
                    },
                    "reason": {
                        "type": "string",
                        "description": "退货原因，例如：不喜欢、质量问题、尺码不合适等",
                    },
                },
                "required": ["order_id", "reason"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "get_return_policy",
            "description": "获取退货退款政策详情",
            "parameters": {"type": "object", "properties": {}},
        },
    },
    {
        "type": "function",
        "function": {
            "name": "recommend_products",
            "description": "根据用户需求推荐合适的商品",
            "parameters": {
                "type": "object",
                "properties": {
                    "keyword": {
                        "type": "string",
                        "description": "搜索关键词，例如：耳机、充电宝",
                    },
                    "category": {
                        "type": "string",
                        "description": "商品类别，例如：耳机、手表",
                    },
                    "max_price": {
                        "type": "number",
                        "description": "最高预算（元）",
                    },
                    "top_n": {
                        "type": "integer",
                        "description": "返回推荐数量，默认3",
                        "default": 3,
                    },
                },
                "required": [],
            },
        },
    },
]

TOOL_DISPATCH = {
    "query_order": query_order,
    "initiate_return": initiate_return,
    "get_return_policy": get_return_policy,
    "recommend_products": recommend_products,
}
