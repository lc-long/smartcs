from __future__ import annotations

from langchain_core.tools import tool


@tool
async def faq_search(query: str, top_k: int = 3) -> str:
    """搜索常见问题FAQ。

    Args:
        query: 搜索问题
        top_k: 返回结果数量
    """
    faqs = [
        {
            "question": "如何重置密码？",
            "answer": "在登录页面点击'忘记密码'，输入注册邮箱，系统会发送重置链接。",
            "category": "账户",
        },
        {
            "question": "如何联系客服？",
            "answer": "您可以通过在线聊天、电话(400-xxx-xxxx)或邮件(support@example.com)联系我们。",
            "category": "通用",
        },
        {
            "question": "退换货政策是什么？",
            "answer": "自收到商品起30天内，商品未使用且包装完好的情况下可申请无理由退换货。",
            "category": "售后",
        },
        {
            "question": "如何查看订单物流？",
            "answer": "登录账户后，在'我的订单'页面可查看所有订单的物流状态。",
            "category": "订单",
        },
        {
            "question": "会员权益有哪些？",
            "answer": "会员享受积分累计、专属折扣、生日礼品、优先客服等权益。",
            "category": "会员",
        },
    ]

    results = []
    query_lower = query.lower()
    for faq in faqs:
        if (query_lower in faq["question"].lower()
                or query_lower in faq["answer"].lower()
                or query_lower in faq["category"].lower()):
            results.append(faq)

    if not results:
        results = faqs[:top_k]

    import json
    return json.dumps(results[:top_k], ensure_ascii=False)


@tool
async def company_info(info_type: str = "general") -> str:
    """查询公司基本信息。

    Args:
        info_type: 信息类型 (general/contact/business_hours/address)
    """
    info = {
        "general": {
            "name": "SmartCS科技有限公司",
            "description": "专注于智能硬件和AI客服解决方案的科技公司",
            "founded": "2020年",
        },
        "contact": {
            "phone": "400-xxx-xxxx",
            "email": "support@example.com",
            "wechat": "SmartCS_official",
        },
        "business_hours": {
            "weekdays": "09:00 - 18:00",
            "weekends": "10:00 - 16:00",
            "holidays": "休息",
        },
        "address": {
            "city": "北京市",
            "district": "海淀区",
            "detail": "中关村科技园xxx号",
        },
    }

    result = info.get(info_type, info["general"])
    import json
    return json.dumps(result, ensure_ascii=False)
