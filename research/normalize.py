# -*- coding: utf-8 -*-
"""第26步：商品证据模型及准入门槛。不从搜索页推定到手价。"""
from __future__ import annotations
from dataclasses import asdict, dataclass
from decimal import Decimal, InvalidOperation
from urllib.parse import urlparse
from typing import Optional

PLATFORM_TYPES = {
    "1688": "批发",
    "闲鱼": "二手",
    "盼之代售": "游戏账号",
}

@dataclass(frozen=True)
class Candidate:
    平台: str
    详情链接: str
    标题: str
    规格: str = ""
    页面标价: Optional[str] = None
    运费: Optional[str] = None
    附加费用: Optional[str] = None
    优惠: Optional[str] = None
    起订量: Optional[int] = None
    货品成色: str = ""
    账号区服: str = ""
    账号安全核验: bool = False
    价格来源时间: str = ""
    人工核对规格: bool = False
    人工核对实际费用: bool = False

def money(value) -> Optional[Decimal]:
    if value is None or str(value).strip() == "":
        return None
    try:
        d = Decimal(str(value))
        if not d.is_finite() or d < 0:
            return None
        return d
    except (InvalidOperation, ValueError):
        return None

def normalize(record: Candidate) -> dict:
    """保守筛选：没有完整证明就不提供可购买金额。"""
    result = asdict(record)
    result.update({"分类": PLATFORM_TYPES.get(record.平台,"普通商品"),
                   "证据状态": "需人工核验", "可进入正式推荐": False,
                   "到手价": None, "风险原因": []})
    reasons = result["风险原因"]
    u = urlparse(record.详情链接)
    allowed_host = {
        "1688": ("1688.com",),
        "闲鱼": ("goofish.com",),
        "盼之代售": ("pzds.com",),
    }.get(record.平台, ())
    host = (u.hostname or "").lower()
    if not (u.scheme == "https" and any(host == base or host.endswith("." + base) for base in allowed_host)):
        reasons.append("商品链接不是对应平台的HTTPS地址")
    if not record.标题.strip():
        reasons.append("缺少商品标题")
    if not record.规格.strip():
        reasons.append("未确认具体规格")
    p = money(record.页面标价)
    ship, extra, discount = (money(record.运费),money(record.附加费用),money(record.优惠))
    if any(v is None for v in (p,ship,extra,discount)):
        reasons.append("页面标价、运费、服务费或优惠信息不完整")
    elif discount > p + ship + extra:
        reasons.append("优惠金额异常")
    if record.平台 == "1688" and (record.起订量 is None or record.起订量 < 1):
        reasons.append("未核实最低起订量")
    if record.平台 == "闲鱼" and not record.货品成色.strip():
        reasons.append("未核实二手成色")
    if record.平台 == "盼之代售":
        if not record.账号区服.strip():
            reasons.append("未核实账号游戏区服")
        if not record.账号安全核验:
            reasons.append("账号实名、换绑与找回风险未完成核验")
    if not record.价格来源时间:
        reasons.append("缺少核价时间")
    if not record.人工核对规格:
        reasons.append("规格未经人工核验")
    if not record.人工核对实际费用:
        reasons.append("费用未经人工核验")
    if not reasons:
        quantity = record.起订量 if record.平台 == "1688" else 1
        result["到手价"] = str((p * quantity + ship + extra - discount).quantize(Decimal("0.01")))
        result["证据状态"] = "人工核验通过（非平台担保）"
        result["可进入正式推荐"] = True
    return result
