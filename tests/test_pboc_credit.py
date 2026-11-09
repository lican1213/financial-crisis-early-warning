"""PBOC credit adversarial source/grain tests: a government copy is NOT original vintage."""
import unittest
from datetime import date,datetime,timezone
from fcews.pboc_credit import FINANCIAL,CREDIT,collect,parse_financial,parse_credit,exact_source

TODAY=date(2026,11,9)
F="""<html><p>2026年前三季度金融统计数据报告</p>
<p>信息来源：中国人民银行 发布时间：2026-10-15</p>
<p>二、前三季度社会融资规模增量累计为27.46万亿元</p>
<p>初步统计，2026年前三季度社会融资规模增量累计为27.46万亿元，比上年同期少2.63万亿元。其中，对实体经济发放的人民币贷款增加11.5万亿元，同比少增3.04万亿元；政府债券净融资10.3万亿元，同比少1.16万亿元。</p>
<p>五、前三季度人民币贷款增加11.52万亿元</p>
<p>前三季度人民币贷款增加11.52万亿元。分部门看，住户贷款减少1.03万亿元，其中，短期贷款减少1.14万亿元，中长期贷款增加1062亿元；企（事）业单位贷款增加12.55万亿元，其中，短期贷款增加4.64万亿元，中长期贷款增加6.53万亿元，票据融资增加1.24万亿元；非银行业金融机构贷款减少5865亿元。</p></html>"""
C="""<html><h1>2026年三季度金融机构贷款投向统计报告</h1>
<p>信息来源：中国人民银行 发布时间：2026-10-29</p>
<h2>六、房地产贷款有所放缓</h2>
<p>2026年三季度末，人民币房地产贷款余额50.08万亿元，同比下降5.2%，前三季度减少1.90万亿元。</p>
<p>2026年三季度末，房地产开发贷款余额12.37万亿元，同比下降9.1%，前三季度减少8179亿元。个人住房贷款余额35.91万亿元，同比下降4.1%，前三季度减少1.10万亿元。</p>
<h2>七、贷款支持科创企业力度保持稳定</h2>
<p>普惠小微企业贷款另有专项统计。</p>
<h2>八、住户经营性贷款同比小幅增长</h2>
<p>2026年三季度末，本外币住户贷款余额82.25万亿元，同比下降2.0%，前三季度减少1.03万亿元。其中，经营性贷款余额25.64万亿元，同比增长1.7%，前三季度增加5383亿元。不含个人住房贷款的消费性贷款余额20.69万亿元，同比下降2.8%，前三季度减少4736亿元。</p></html>"""


class PBOCGates(unittest.TestCase):
    def test_official_shanghai_gov_reprint_but_not_original_pbc(self):
        self.assertTrue(exact_source(FINANCIAL,"financial"))
        self.assertTrue(exact_source(CREDIT,"credit"))
        for bad in [
            "http://jrj.sh.gov.cn/SCGK194/20261015/24a15f78c09947de9eb58a48c2fdb451.html",
            "https://jrj.sh.gov.cn.evil.test/SCGK194/20261015/24a15f78c09947de9eb58a48c2fdb451.html",
            "https://jrj.sh.gov.cn@evil.test/SCGK194/20261015/24a15f78c09947de9eb58a48c2fdb451.html",
        ]:
            self.assertFalse(exact_source(bad,"financial"))

    def test_gov_bonds_are_not_private_credit(self):
        x=parse_financial(F,TODAY)
        self.assertEqual(x["household_medium_long_ytd_flow_100m_cny"],1062)
        self.assertEqual(x["household_total_ytd_flow_trillion_cny"],-1.03)
        self.assertEqual(x["corporate_medium_long_ytd_flow_trillion_cny"],6.53)
        self.assertEqual(x["corporate_bill_financing_ytd_flow_trillion_cny"],1.24)
        self.assertAlmostEqual(x["gov_bond_fraction_of_tsf_pct"],37.51,places=2)
        self.assertIsNone(x["private_credit_impulse"])
        self.assertIsNone(x["original_PBOC_publication_timestamp"])

    def test_household_medium_long_cannot_equal_mortgage_flow(self):
        f=parse_financial(F,TODAY)
        c=parse_credit(C,TODAY)
        self.assertEqual(f["household_medium_long_ytd_flow_100m_cny"],1062)
        self.assertEqual(c["individual_mortgage_ytd_net_change_trillion_cny"],-1.10)
        self.assertEqual(c["individual_mortgage_balance_yoy_pct"],-4.1)
        self.assertEqual(c["individual_mortgage_balance_trillion_cny"],35.91)
        self.assertIsNone(c["mlt_consumption_loan_ytd_flow"])
        self.assertIsNone(c["mortgage_prepayment_volume"])
        self.assertNotEqual(f["household_medium_long_ytd_flow_100m_cny"]/10000,
                            c["individual_mortgage_ytd_net_change_trillion_cny"])

    def test_developer_received_mortgage_not_household_mortgage(self):
        c=parse_credit(C,TODAY)
        self.assertEqual(c["real_estate_developer_LOAN_balance_trillion_cny"],12.37)
        self.assertIn("not_NBS_developer_received",c["statistical_entity"])
        self.assertEqual(c["household_business_loan_balance_trillion_cny"],25.64)
        self.assertEqual(c["household_nonmortgage_consumption_balance_trillion_cny"],20.69)

    def test_future_and_forged_source_fail_closed(self):
        with self.assertRaises(ValueError):
            parse_credit(C,date(2026,10,28))
        with self.assertRaises(ValueError):
            parse_financial(F.replace("发布时间：2026-10-15","发布时间：2026-11-10"),TODAY)
        with self.assertRaises(ValueError):
            parse_financial(F.replace("信息来源：中国人民银行","信息来源：金融广告"),TODAY)

    def test_missing_credit_categories_and_wrong_quarter_rejected(self):
        with self.assertRaises(ValueError):
            parse_credit(C.replace("个人住房贷款余额35.91万亿元","开发商收到个人按揭贷款35.91万亿元"),TODAY)
        with self.assertRaises(ValueError):
            parse_financial(F.replace("2026年前三季度金融统计数据报告","2026年上半年金融统计数据报告"),TODAY)
        with self.assertRaises(ValueError):
            parse_financial(F.replace("中长期贷款增加1062亿元","中长期贷款增加99999亿元"),TODAY)

    def test_full_repub_pair_same_period_no_macro_score_or_crisis(self):
        inputs={FINANCIAL:F,CREDIT:C}
        out=collect(datetime(2026,11,9,tzinfo=timezone.utc),lambda url,timeout:inputs[url])
        self.assertEqual(out["status"],"complete")
        self.assertEqual(out["period_end"],"2026-09-30")
        self.assertFalse(out["housing_turning_point_confirmed"])
        self.assertFalse(out["risk_alert_authorized"])
        self.assertIsNone(out["china_recovery_breadth_score"])
        self.assertEqual(out["source_quality"],"government_republication_not_original_first_publication_vintage")


if __name__=="__main__":
    unittest.main()
