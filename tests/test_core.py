import unittest
from datetime import date
from fcews.core import Observation, decide, fresh, indicators
from fcews.collect import parse_fred_csv
DAY = date(2026, 10, 28)
BASE = {"severity": "green", "critical_families": [], "seen_events": [], "last_alert_severity": "green"}

def obs(code, value, day="2026-10-27"):
    return Observation(code, day, value, "https://fred.stlouisfed.org/series/" + code, "utc")

def calm(day="2026-10-27"):
    return {"STLFSI4": obs("STLFSI4", -0.6, day),
            "VIXCLS": obs("VIXCLS", 17, day),
            "BAMLH0A0HYM2": obs("BAMLH0A0HYM2", 3, day)}

class AuditTests(unittest.TestCase):
    def test_fred_csv_with_latest_missing(self):
        r = parse_fred_csv("VIXCLS", "DATE,VIXCLS\n2026-10-26,18\n2026-10-27,.\n", "utc")
        self.assertEqual((r.date, r.value), ("2026-10-26", 18))
    def test_bad_csv(self):
        with self.assertRaises(ValueError):
            parse_fred_csv("SOFR", "DATE,VIXCLS\n2026-10-27,17\n", "utc")
    def test_stale_and_future_rejected(self):
        self.assertFalse(fresh(obs("VIXCLS", 50, "2026-09-01"), DAY))
        self.assertFalse(fresh(obs("VIXCLS", 50, "2026-10-29"), DAY))
    def test_stale_signal_cannot_trigger(self):
        r=decide({"VIXCLS":obs("VIXCLS",50,"2026-09-01")},BASE,{"severity":"green"},[],DAY)
        self.assertEqual(r["severity"],"unknown")
        self.assertFalse(r["alert"])
    def test_bootstrap_dual_family_alert(self):
        r=decide({"VIXCLS":obs("VIXCLS",40),"BAMLH0A0HYM2":obs("BAMLH0A0HYM2",7)}, {}, {}, [], DAY)
        self.assertTrue(r["alert"])
    def test_system_family_not_double_counted(self):
        r=decide({"STLFSI4":obs("STLFSI4",2),"NFCI":obs("NFCI",2)},BASE,{},[],DAY)
        self.assertNotIn("independent_stress_families",r["reasons"])
    def test_calm_silent(self):
        self.assertFalse(decide(calm(),BASE,{"severity":"green"},[],DAY)["alert"])
    def test_single_family_cannot_trigger_weekly(self):
        self.assertFalse(decide({"VIXCLS":obs("VIXCLS",40)},BASE,{"severity":"green"},[],DAY)["alert"])
    def test_weekly_escalation(self):
        r=decide({**calm(),"VIXCLS":obs("VIXCLS",40)},BASE,{"severity":"green"},[],DAY)
        self.assertIn("above_weekly_baseline",r["reasons"])
    def test_unknown_weekly_cannot_fabricate_upgrade(self):
        self.assertFalse(decide({**calm(),"VIXCLS":obs("VIXCLS",40)},BASE,{},[],DAY)["alert"])
    def test_duplicate_stress_silent(self):
        rows={"VIXCLS":obs("VIXCLS",40),"BAMLH0A0HYM2":obs("BAMLH0A0HYM2",7)}
        first=decide(rows,{}, {},[],DAY)
        self.assertFalse(decide(rows,first["next_state"],{},[],DAY)["alert"])
    def test_funding_mismatched_date(self):
        rows={"SOFR":obs("SOFR",4.1),"TGCR":obs("TGCR",3.9,"2026-10-26")}
        self.assertNotIn("SOFR_TGCR_SPREAD",indicators(rows,DAY))
    def test_funding_units(self):
        rows={"SOFR":obs("SOFR",4.1),"TGCR":obs("TGCR",3.9)}
        self.assertTrue(indicators(rows,DAY)["SOFR_TGCR_SPREAD"]["critical"])
    def test_rumor_not_accepted(self):
        ev=[{"id":"a","verified":False,"primary_source_url":"https://example.com","cross_market_mechanism":"contagion"}]
        self.assertFalse(decide({},BASE,{},ev,DAY)["alert"])
    def test_event_once(self):
        ev=[{"id":"a","verified":True,"primary_source_url":"https://example.com/filing","cross_market_mechanism":"contagion"}]
        r=decide({},BASE,{},ev,DAY)
        self.assertTrue(r["alert"])
        self.assertFalse(decide({},r["next_state"],{},ev,DAY)["alert"])
    def test_same_hourly_data_not_three_recoveries(self):
        state={}
        for i in range(6):
            r=decide(calm(),state,{"severity":"orange"},[],DAY)
            state=r["next_state"]
        self.assertEqual(state["recovery_count"],1)
        self.assertFalse(r["alert"])
    def test_three_distinct_dates_recovery(self):
        state={}
        for day in ("2026-10-26","2026-10-27","2026-10-28"):
            r=decide(calm(day),state,{"severity":"orange"},[],DAY)
            state=r["next_state"]
        self.assertIn("sustained_recovery",r["reasons"])
        self.assertFalse(decide(calm("2026-10-28"),state,{"severity":"orange"},[],DAY)["alert"])
    def test_recovery_reset_on_new_pressure(self):
        r=decide(calm("2026-10-26"),{},{"severity":"orange"},[],DAY)
        risk={**calm(),"VIXCLS":obs("VIXCLS",40),"BAMLH0A0HYM2":obs("BAMLH0A0HYM2",7)}
        self.assertEqual(decide(risk,r["next_state"],{"severity":"orange"},[],DAY)["next_state"]["recovery_count"],0)
    def test_bad_weekly_label(self):
        with self.assertRaises(ValueError):
            decide(calm(),{},{"severity":"bad"},[],DAY)

if __name__ == "__main__":
    unittest.main()
