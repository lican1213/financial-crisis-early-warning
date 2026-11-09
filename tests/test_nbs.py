"""Fail-closed NBS article extraction: wrong section, fake dates, unsafe URLs."""
import unittest
from datetime import date, datetime, timezone

from fcews.nbs import collect, discover_pmi, parse_pmi, valid_article

URL="https://www.stats.gov.cn/sj/zxfbhjd/202610/t20261031_1965718.html"
INDEX="""<html><a href="./202609/t20260930_1965555.html">2026年9月中国采购经理指数运行情况</a>
<a href="./202610/t20261031_1965718.html">2026年10月中国采购经理指数运行情况</a>
<a href="https://www.stats.gov.cn.evil.example/sj/zxfbhjd/202611/t20261130_999.html">2026年11月中国采购经理指数运行情况</a>
<a href="./202610/fake.html">2026年12月中国采购经理指数运行情况</a></html>"""
ARTICLE="""<html><div>2026/10/31 09:30</div>
<h1>2026年10月中国采购经理指数运行情况</h1>
<h2>一、中国制造业采购经理指数运行情况</h2>
<p>10月份，制造业采购经理指数（PMI）为49.3%，比上月下降0.8个百分点。</p>
<p>从企业规模看，大型企业PMI为50.2%；中、小型企业PMI分别为48.4%和47.5%，低于临界点。</p>
<p>生产指数为49.8%，比上月下降1.9个百分点。</p>
<p>新订单指数为49.4%，比上月下降1.1个百分点。</p>
<h2>二、中国非制造业采购经理指数运行情况</h2>
<p>新订单指数为44.4%，比上月下降。</p>
</html>"""


class NBSPMIPrimaryGates(unittest.TestCase):
    def setUp(self):
        self.today=date(2026,11,9)

    def test_official_index_picks_newest_not_future_spoof(self):
        self.assertEqual(discover_pmi(INDEX,self.today),(URL,2026,10))

    def test_exact_manufacturing_section_and_release_period(self):
        x=parse_pmi(ARTICLE,URL,2026,10,self.today)
        self.assertEqual({k: v["value"] for k,v in x["observations"].items()},
                         {"NBS_PMI_MANUFACTURING":49.3,
                          "NBS_PMI_NEW_ORDERS":49.4,"NBS_PMI_SMALL":47.5})
        self.assertEqual(x["released_at_date"],"2026-10-31")
        self.assertEqual(x["observations"]["NBS_PMI_NEW_ORDERS"]["period_end"],"2026-10-31")
        self.assertFalse(x["alert_authorized"])
        self.assertFalse(x["score_authorized"])

    def test_future_index_release_not_used(self):
        with self.assertRaises(ValueError):
            discover_pmi('<a href="./202612/t20261231_9999.html">2026年12月中国采购经理指数运行情况</a>',self.today)

    def test_future_published_article_rejected(self):
        text=ARTICLE.replace("2026/10/31 09:30","2026/11/10 09:30")
        with self.assertRaises(ValueError):
            parse_pmi(text,URL,2026,10,self.today)

    def test_wrong_section_demand_cannot_substitute_for_manufacturing(self):
        text=ARTICLE.replace("新订单指数为49.4%","原材料价格指数为49.4%")
        with self.assertRaises(ValueError):
            parse_pmi(text,URL,2026,10,self.today)

    def test_bad_title_or_unknown_release_period_rejected(self):
        with self.assertRaises(ValueError):
            parse_pmi(ARTICLE.replace("2026年10月中国采购经理指数运行情况","2025年10月中国采购经理指数运行情况"),URL,2026,10,self.today)
        with self.assertRaises(ValueError):
            parse_pmi(ARTICLE,URL,2026,11,self.today)

    def test_number_150_not_silent_success(self):
        with self.assertRaises(ValueError):
            parse_pmi(ARTICLE.replace("49.3%","150%"),URL,2026,10,self.today)

    def test_impostor_host_and_encoded_credentials_rejected(self):
        self.assertFalse(valid_article("https://www.stats.gov.cn.evil.example/sj/zxfbhjd/202610/t20261031_1965718.html"))
        self.assertFalse(valid_article("https://stats.gov.cn@evil.example/sj/zxfbhjd/202610/t20261031_1965718.html"))
        self.assertFalse(valid_article("http://www.stats.gov.cn/sj/zxfbhjd/202610/t20261031_1965718.html"))

    def test_fetcher_reads_both_official_original_pages(self):
        seen=[]
        def fake(url,timeout):
            seen.append(url)
            return INDEX if url.endswith("/sj/zxfbhjd/") else ARTICLE
        x=collect(datetime(2026,11,9,tzinfo=timezone.utc),fake)
        self.assertEqual(seen,["https://www.stats.gov.cn/sj/zxfbhjd/",URL])
        self.assertEqual(x["status"],"complete")


if __name__=="__main__":
    unittest.main()
