# -*- coding: utf-8 -*-
import sys
import unittest
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "research"))
from public_probe import PLATFORMS, host_allowed, analyze_html
from normalize import Candidate, money, normalize

class EvidenceTests(unittest.TestCase):
    def test_domains_no_similar_host_attack(self):
        self.assertTrue(host_allowed("detail.1688.com",("1688.com",)))
        self.assertFalse(host_allowed("1688.com.evil.example",("1688.com",)))
    def test_platform_entries(self):
        self.assertEqual(set(PLATFORMS), {"1688","闲鱼","盼之代售"})
        self.assertIn("keywords=",PLATFORMS["1688"]["entry"])
    def test_extract_public_link_not_price(self):
        doc=b'<html><head><title>Test</title></head><body><a href="/item?id=123">product</a></body></html>'
        r=analyze_html(doc,"https://www.goofish.com/search",PLATFORMS["闲鱼"])
        self.assertEqual(r["发现详情链接数"],1)
        self.assertNotIn("到手价",r)
    def test_reject_forged_host(self):
        d=Candidate("闲鱼","https://www.goofish.com.evil.test/item?id=10","耳机","黑色", "70","0","0","0",
                   货品成色="近全新",价格来源时间="2026-11-06",人工核对规格=True,人工核对实际费用=True)
        self.assertFalse(normalize(d)["可进入正式推荐"])
    def test_money_invalid(self):
        self.assertIsNone(money("NaN"))
        self.assertIsNone(money("-10"))
        self.assertIsNone(money(None))
    def test_1688_requires_moq(self):
        d=Candidate("1688","https://detail.1688.com/offer/123.html","耳机","黑色","10","5","0","0",
                    价格来源时间="2026-11-06",人工核对规格=True,人工核对实际费用=True)
        self.assertIn("未核实最低起订量",normalize(d)["风险原因"])
    def test_wholesale_total_uses_qty(self):
        d=Candidate("1688","https://detail.1688.com/offer/123.html","耳机","黑色","10","5","0","2",
                    起订量=3,价格来源时间="2026-11-06",人工核对规格=True,人工核对实际费用=True)
        self.assertEqual(normalize(d)["到手价"],"33.00")
    def test_pzds_safety_is_required(self):
        d=Candidate("盼之代售","https://www.pzds.com/detail/10","游戏账号","王者荣耀","800","0","0","0",
                    账号区服="安卓",价格来源时间="2026-11-06",人工核对规格=True,人工核对实际费用=True)
        self.assertFalse(normalize(d)["可进入正式推荐"])
    def test_xianyu_condition_required(self):
        d=Candidate("闲鱼","https://www.goofish.com/item?id=10","耳机","黑色","70","0","0","0",
                    价格来源时间="2026-11-06",人工核对规格=True,人工核对实际费用=True)
        self.assertFalse(normalize(d)["可进入正式推荐"])
    def test_unknown_shipping_must_not_rank(self):
        d=Candidate("闲鱼","https://www.goofish.com/item?id=10","耳机","黑色","70",None,"0","0",
                    货品成色="近全新",价格来源时间="2026-11-06",人工核对规格=True,人工核对实际费用=True)
        self.assertIsNone(normalize(d)["到手价"])

if __name__ == "__main__":
    unittest.main()
