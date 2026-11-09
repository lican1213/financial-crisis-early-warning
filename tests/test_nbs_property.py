"""Property-source red team: incomplete 70-city tables never become national breadth."""
import re
import unittest
from datetime import date, datetime, timezone
from unittest.mock import patch

from fcews.nbs_property import (
    CITIES, INDEX, SEEDS, collect, discover, parse_prices,
    parse_market, official_page, signed_change, read_large_nbs_page,
)

TODAY=date(2026,11,9)
P09=SEEDS["price"][0]
P08=SEEDS["price"][1]
M09=SEEDS["market"][0]
M08=SEEDS["market"][1]


def price_page(month=9,used_up=9,new_up=17,omit=None,duplicate=None):
    left=CITIES[:35]
    right=CITIES[35:]
    def table(kind,up):
        cities={}
        for i,name in enumerate(CITIES):
            if name==omit:continue
            cities[name]=(100.2 if i<up else 99.5, 96.0,95.0)
        rows=[]
        for a,b in zip(left,right):
            if a in cities and b in cities:
                va,vb=cities[a],cities[b]
                rows.append("<tr><td>"+a+"</td>"+ "".join("<td>"+str(x)+"</td>" for x in va)
                            +"<td>"+b+"</td>"+"".join("<td>"+str(x)+"</td>" for x in vb)+"</tr>")
        if duplicate:
            rows.append("<tr><td>"+duplicate+"</td><td>100.1</td><td>95.0</td><td>94.0</td></tr>")
        return "<table>"+"".join(rows)+"</table>"
    return ('<html><p>2026/'+("10/19" if month==9 else "09/15")+' 09:30</p>'
            +f'<h1>2026年{month}月份70个大中城市商品住宅销售价格变动情况</h1>'
            +f'<p>表1：2026年{month}月70个大中城市新建商品住宅销售价格指数</p>'
            +table("new",new_up)
            +f'<p>表2：2026年{month}月70个大中城市二手住宅销售价格指数</p>'
            +table("used",used_up)
            +f'<p>表3：2026年{month}月70个大中城市新建商品住宅销售价格分类指数（一）</p></html>')


def market_page(month=9,res_area="-13.8",funds="-22.1",inventory="-1.5"):
    def wording(x):
        return "下降"+x[1:]+"%" if x.startswith("-") else "增长"+x+"%"
    return f"""<html><span>2026/{'10/19' if month==9 else '09/15'} 10:00</span>
      <h1>2026年1—{month}月份全国房地产市场基本情况</h1>
      <h2>一、房地产开发投资完成情况</h2><p>房地产开发投资53364亿元，同比下降20.6%。</p>
      <h2>二、商品房销售和待售情况</h2><p>1—{month}月份，新建商品房销售面积56483万平方米，同比下降13.2%；其中住宅销售面积{wording(res_area)}。新建商品房销售额53799亿元，下降13.9%；其中住宅销售额下降13.7%。</p>
      <p>{month}月末，新建商品房待售面积74825万平方米，同比{wording(inventory)}。</p>
      <h2>三、房地产开发企业到位资金情况</h2>
      <p>1—{month}月份，房地产开发企业到位资金56813亿元，同比下降21.6%。其中，国内贷款7624亿元，下降33.1%；自筹资金20572亿元，下降21.4%；定金及预收款17982亿元，下降14.8%；个人按揭贷款7678亿元，{wording(funds)}。</p>
      <h3>表1 2026年1—{month}月份全国房地产开发和销售情况</h3>
      </html>"""


class CensusTests(unittest.TestCase):
    def test_exact_seventy_city_full_census(self):
        got=parse_prices(price_page(),P09,TODAY)
        self.assertEqual(got["new"]["mom_rising"],17)
        self.assertEqual(got["used"]["mom_rising"],9)
        self.assertEqual(got["used"]["mom_falling"],61)
        self.assertEqual(len(got["used"]["cities"]),70)
        self.assertEqual(got["period_end"],"2026-09-30")

    def test_duplicate_or_missing_city_never_accepted(self):
        for kw in ({"omit":"北京"},{"duplicate":"北京"}):
            with self.assertRaises(ValueError):
                parse_prices(price_page(**kw),P09,TODAY)

    def test_used_home_is_not_new_home_and_yoy_is_not_mom(self):
        raw=price_page(used_up=5,new_up=28)
        got=parse_prices(raw,P09,TODAY)
        self.assertEqual((got["new"]["mom_rising"],got["used"]["mom_rising"]),(28,5))
        self.assertEqual(got["new"]["yoy_rising"],0)
        self.assertEqual(got["new"]["mom_rising"],28)

    def test_fake_official_hostname_and_missing_table(self):
        self.assertFalse(official_page("https://www.stats.gov.cn.evil.tld/sj/zxfb/202610/t20261019_1965609.html"))
        self.assertFalse(official_page("http://www.stats.gov.cn/sj/zxfb/202610/t20261019_1965609.html"))
        with self.assertRaises(ValueError):
            parse_prices(price_page().replace("表2：","表4："),P09,TODAY)

    def test_future_or_wrong_month_article(self):
        with self.assertRaises(ValueError):
            parse_prices(price_page().replace("2026/10/19 09:30","2026/11/10 09:30"),P09,TODAY)
        with self.assertRaises(ValueError):
            parse_prices(price_page().replace("2026年9月份","2027年9月份"),P09,TODAY)

    def test_market_funding_is_developer_receipts_not_home_credit(self):
        got=parse_market(market_page(),M09,TODAY)
        self.assertEqual(got["residential_sales_area_yoy_pct"],-13.8)
        self.assertEqual(got["new_homes_unsold_area_yoy_pct"],-1.5)
        self.assertEqual(got["developer_funding"]["developer_received_mortgages"]["cumulative_yoy_pct"],-22.1)
        self.assertEqual(got["developer_funding"]["developer_received_mortgages"]["amount_100m_cny"],7678)
        self.assertIn("not_household_credit",got["developer_funding"]["developer_received_mortgages"]["statistical_entity"])
        self.assertIn("NOT PBOC",got["credit_warning"])

    def test_sales_and_funding_mixed_sections_rejected(self):
        with self.assertRaises(ValueError):
            parse_market(market_page().replace("个人按揭贷款7678亿元","企业贷款7678亿元"),M09,TODAY)
        with self.assertRaises(ValueError):
            parse_market(market_page().replace("其中住宅销售面积下降13.8%","其中住宅销售面积增加13.8%"),M09,TODAY)

    def test_signed_not_guessing(self):
        self.assertEqual(signed_change("下降20.6%"),-20.6)
        self.assertEqual(signed_change("增长10.7%"),10.7)
        with self.assertRaises(ValueError):
            signed_change("提升十个百分点")

    def test_two_periods_and_turning_point_fails_without_pbc(self):
        urls={P09:price_page(9,used_up=9),P08:price_page(8,used_up=3,new_up=15),
              M09:market_page(9),M08:market_page(8,res_area="-13.0",funds="-22.4",inventory="-1.1")}
        def fake(url,timeout):
            if url==INDEX:
                return "<html><a href='/sj/zxfb/202610/t20261019_1965609.html'>2026年9月份70个大中城市商品住宅销售价格变动情况</a></html>"
            return urls[url]
        got=collect(datetime(2026,11,9,tzinfo=timezone.utc),fake)
        self.assertEqual(got["status"],"complete")
        self.assertEqual(got["directional_signals"]["used_price_rising_city_count_change"],6)
        self.assertEqual(got["directional_signals"]["residential_sales_cumulative_yoy_pp_change"],-0.8)
        self.assertFalse(got["housing_turning_point_confirmed"])
        self.assertIsNone(got["china_recovery_breadth_score"])


    def test_large_original_html_above_generic_FRED_limit_is_bounded(self):
        class FakeResponse:
            def __init__(self,url,data):
                self.url,self.data=url,data
            def __enter__(self):return self
            def __exit__(self,*args):return False
            def geturl(self):return self.url
            def read(self,n):return self.data[:n]
        legit=b"a"*1_000_100
        with patch("fcews.nbs_property.urlopen",return_value=FakeResponse(P09,legit)):
            self.assertEqual(len(read_large_nbs_page(P09)),1_000_100)
        with patch("fcews.nbs_property.urlopen",return_value=FakeResponse(P09,b"a"*12_000_001)):
            with self.assertRaises(ValueError):
                read_large_nbs_page(P09)

    def test_official_nbs_http_redirect_cannot_escape_allowed_host(self):
        class Redirect:
            def __enter__(self):return self
            def __exit__(self,*args):return False
            def geturl(self):return "https://www.stats.gov.cn.evil.test/sj/zxfb/202610/t20261019_1965609.html"
            def read(self,n):return b""
        with patch("fcews.nbs_property.urlopen",return_value=Redirect()):
            with self.assertRaises(ValueError):
                read_large_nbs_page(P09)

    def test_index_only_future_or_spoofed_discarded(self):
        html="<a href='https://www.stats.gov.cn.evil.test/sj/zxfb/202611/t20261109_123.html'>2026年11月份70个大中城市商品住宅销售价格变动情况</a>"
        self.assertEqual(discover(html,"price",TODAY),[])


if __name__=="__main__":
    unittest.main()
