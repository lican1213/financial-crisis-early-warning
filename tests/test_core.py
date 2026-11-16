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
        r=decide({"VIXCLS":obs("VIXCLS",50,"2026-09-01")},BASE,{"severity":"green","as_of":"2026-10-25","source_url":"https://www.federalreserve.gov/"},[],DAY)
        self.assertEqual(r["severity"],"unknown")
        self.assertFalse(r["alert"])
    def test_bootstrap_dual_family_alert(self):
        r=decide({"VIXCLS":obs("VIXCLS",40),"BAMLH0A0HYM2":obs("BAMLH0A0HYM2",7)}, {}, {}, [], DAY)
        self.assertTrue(r["alert"])
    def test_system_family_not_double_counted(self):
        r=decide({"STLFSI4":obs("STLFSI4",2),"NFCI":obs("NFCI",2)},BASE,{},[],DAY)
        self.assertNotIn("independent_stress_families",r["reasons"])
    def test_composite_plus_single_direct_channel_is_not_two_independent_votes(self):
        for composite in ("OFR_FSI", "STLFSI4", "NFCI", "ANFCI"):
            for direct, value in (("VIXCLS", 40), ("BAMLH0A0HYM2", 7)):
                with self.subTest(composite=composite, direct=direct):
                    r=decide({composite:obs(composite,2),direct:obs(direct,value)},BASE,{},[],DAY)
                    self.assertEqual(len(r["critical_families"]),2)
                    self.assertEqual(r["confirming_families"],[])
                    self.assertFalse(r["alert"])

    def test_composite_does_not_block_first_genuine_direct_pair(self):
        prior={"critical_families":["system","volatility"]}
        rows={"OFR_FSI":obs("OFR_FSI",2),"VIXCLS":obs("VIXCLS",40),"BAMLH0A0HYM2":obs("BAMLH0A0HYM2",7)}
        r=decide(rows,prior,{},[],DAY)
        self.assertEqual(r["confirming_families"],["credit","volatility"])
        self.assertEqual(r["confirmation_date"],"2026-10-27")
        self.assertIn("independent_stress_families",r["reasons"])
        self.assertFalse(decide(rows,r["next_state"],{},[],DAY)["alert"])

    def test_direct_channels_on_different_dates_are_not_automatic_confirmation(self):
        rows={"VIXCLS":obs("VIXCLS",40,"2026-10-27"),"BAMLH0A0HYM2":obs("BAMLH0A0HYM2",7,"2026-10-23")}
        self.assertFalse(decide(rows,BASE,{},[],DAY)["alert"])

    def test_funding_and_credit_confirm_without_composite(self):
        rows={"SOFR":obs("SOFR",4.1),"TGCR":obs("TGCR",3.8),"BAMLH0A0HYM2":obs("BAMLH0A0HYM2",7)}
        r=decide(rows,BASE,{},[],DAY)
        self.assertEqual(r["confirming_families"],["credit","funding"])
        self.assertTrue(r["alert"])

    def test_explicitly_uncalibrated_baseline_blocks_legacy_grade_upgrade(self):
        weekly={"severity":"green","as_of":"2026-10-25","source_url":"https://www.federalreserve.gov/","model_comparability":"not_calibrated"}
        self.assertFalse(decide({**calm(),"VIXCLS":obs("VIXCLS",40)},BASE,weekly,[],DAY)["alert"])

    def test_data_gap_does_not_rearm_stress_episode(self):
        risk={"VIXCLS":obs("VIXCLS",40),"BAMLH0A0HYM2":obs("BAMLH0A0HYM2",7)}
        first=decide(risk,BASE,{},[],DAY)
        outage=decide({"VIXCLS":obs("VIXCLS",40)},first["next_state"],{},[],DAY)
        self.assertEqual(outage["confirming_families"],[])
        self.assertEqual(outage["next_state"]["active_confirmation_families"],["credit","volatility"])
        self.assertFalse(decide(risk,outage["next_state"],{},[],DAY)["alert"])

    def test_third_direct_channel_is_new_material_candidate_once(self):
        pair={"VIXCLS":obs("VIXCLS",40),"BAMLH0A0HYM2":obs("BAMLH0A0HYM2",7)}
        first=decide(pair,BASE,{},[],DAY)
        triple={**pair,"SOFR":obs("SOFR",4.1),"TGCR":obs("TGCR",3.8)}
        second=decide(triple,first["next_state"],{},[],DAY)
        self.assertIn("independent_stress_families",second["reasons"])
        self.assertFalse(decide(triple,second["next_state"],{},[],DAY)["alert"])

    def test_only_aligned_new_normal_evidence_rearms_episode(self):
        pair={"VIXCLS":obs("VIXCLS",40),"BAMLH0A0HYM2":obs("BAMLH0A0HYM2",7)}
        first=decide(pair,BASE,{},[],DAY)
        mixed={"VIXCLS":obs("VIXCLS",20,"2026-10-28"),"BAMLH0A0HYM2":obs("BAMLH0A0HYM2",7)}
        pending=decide(mixed,first["next_state"],{},[],DAY)
        self.assertEqual(pending["next_state"]["active_confirmation_families"],["credit","volatility"])
        normal={"VIXCLS":obs("VIXCLS",20,"2026-10-28"),"BAMLH0A0HYM2":obs("BAMLH0A0HYM2",3,"2026-10-28")}
        reset=decide(normal,pending["next_state"],{},[],DAY)
        self.assertEqual(reset["next_state"]["active_confirmation_families"],[])
        rerisk={"VIXCLS":obs("VIXCLS",40,"2026-10-29"),"BAMLH0A0HYM2":obs("BAMLH0A0HYM2",7,"2026-10-29")}
        self.assertTrue(decide(rerisk,reset["next_state"],{},[],date(2026,10,29))["alert"])

    def test_calm_silent(self):
        self.assertFalse(decide(calm(),BASE,{"severity":"green","as_of":"2026-10-25","source_url":"https://www.federalreserve.gov/"},[],DAY)["alert"])
    def test_single_family_cannot_trigger_weekly(self):
        self.assertFalse(decide({"VIXCLS":obs("VIXCLS",40)},BASE,{"severity":"green","as_of":"2026-10-25","source_url":"https://www.federalreserve.gov/"},[],DAY)["alert"])
    def test_weekly_escalation(self):
        r=decide({**calm(),"VIXCLS":obs("VIXCLS",40)},BASE,{"severity":"green","as_of":"2026-10-25","source_url":"https://www.federalreserve.gov/"},[],DAY)
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
    def test_unreviewed_event_true_flag_cannot_trigger(self):
        ev=[{"id":"falsified","verified":True,"primary_source_url":"https://www.fdic.gov/",
             "cross_market_mechanism":"funding contagion"}]
        self.assertFalse(decide({},BASE,{},ev,DAY)["alert"])

    def test_baseline_without_source_stays_unknown(self):
        r=decide({**calm(),"VIXCLS":obs("VIXCLS",40)}, BASE, {"severity":"green"}, [], DAY)
        self.assertNotIn("above_weekly_baseline",r["reasons"])

    def test_event_once(self):
        ev=[{"id":"a","verified":True,"review_status":"approved","verified_by":"human-review", "published_at_utc":"2026-10-27T15:00:00Z", "source_sha256":"a"*64, "primary_source_url":"https://www.fdic.gov/official-statement","cross_market_mechanism":"funding contagion"}]
        r=decide({},BASE,{},ev,DAY)
        self.assertTrue(r["alert"])
        self.assertFalse(decide({},r["next_state"],{},ev,DAY)["alert"])
    def test_same_hourly_data_not_three_recoveries(self):
        state={}
        for i in range(6):
            r=decide(calm(),state,{"severity":"orange","as_of":"2026-10-25","source_url":"https://www.federalreserve.gov/"},[],DAY)
            state=r["next_state"]
        self.assertEqual(state["recovery_count"],1)
        self.assertFalse(r["alert"])
    def test_three_distinct_dates_recovery(self):
        state={}
        for day in ("2026-10-26","2026-10-27","2026-10-28"):
            r=decide(calm(day),state,{"severity":"orange","as_of":"2026-10-25","source_url":"https://www.federalreserve.gov/"},[],DAY)
            state=r["next_state"]
        self.assertIn("sustained_recovery",r["reasons"])
        self.assertFalse(decide(calm("2026-10-28"),state,{"severity":"orange","as_of":"2026-10-25","source_url":"https://www.federalreserve.gov/"},[],DAY)["alert"])
    def test_recovery_reset_on_new_pressure(self):
        r=decide(calm("2026-10-26"),{},{"severity":"orange","as_of":"2026-10-25","source_url":"https://www.federalreserve.gov/"},[],DAY)
        risk={**calm(),"VIXCLS":obs("VIXCLS",40),"BAMLH0A0HYM2":obs("BAMLH0A0HYM2",7)}
        self.assertEqual(decide(risk,r["next_state"],{"severity":"orange","as_of":"2026-10-25","source_url":"https://www.federalreserve.gov/"},[],DAY)["next_state"]["recovery_count"],0)
    def test_recovery_requires_two_new_family_observations(self):
        weekly={"severity":"orange","as_of":"2026-10-25","source_url":"https://www.federalreserve.gov/"}
        rows=calm("2026-10-26")
        one=decide(rows,{},weekly,[],DAY)
        self.assertEqual(one["next_state"]["recovery_count"],1)
        # Only VIXCLS advanced; system and credit dates are unchanged.
        updated={**rows, "VIXCLS":obs("VIXCLS",17,"2026-10-27")}
        two=decide(updated,one["next_state"],weekly,[],DAY)
        self.assertEqual(two["next_state"]["recovery_count"],1)
        self.assertFalse(two["alert"])

    def test_bad_weekly_label(self):
        with self.assertRaises(ValueError):
            decide(calm(),{},{"severity":"bad"},[],DAY)

if __name__ == "__main__":
    unittest.main()
