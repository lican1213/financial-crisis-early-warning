import unittest

from fcews.coverage import audit_event_coverage, classify_misses


def feature(series, value, observed="2020-03-13", available="2020-03-14T00:00:00Z"):
    return {"series": series, "value": str(value), "observation_date": observed,
            "first_available_at_utc": available,
            "availability_basis": "ALFRED_public_asof_plus_one_UTC_day",
            "source_url": "https://alfred.stlouisfed.org/graph/alfredgraph.csv"}


CHECK = [{"decision_at_utc": "2020-03-16T12:00:00Z"}]
EVENT = [{"event_id": "2020-crisis", "crisis_start_utc": "2020-03-16T21:00:00Z"}]


class HistoricalCoverageTests(unittest.TestCase):
    def test_no_inputs_unassessable_not_claimed_miss(self):
        a = audit_event_coverage([], CHECK, EVENT)
        self.assertEqual(a["2020-crisis"]["status"], "unassessable_no_two_family_checkpoint")
        classified = classify_misses(["2020-crisis"], a)
        self.assertEqual(classified["missed_with_three_family_coverage"], [])
        self.assertEqual(classified["unassessable_missing_independent_sources"], ["2020-crisis"])

    def test_two_related_system_indexes_are_one_family(self):
        features = [feature("NFCI", 1), feature("STLFSI4", 2)]
        a = audit_event_coverage(features, CHECK, EVENT)
        self.assertEqual(a["2020-crisis"]["checkpoints_with_two_families"], 0)

    def test_two_family_only_is_not_fully_covered(self):
        features = [feature("NFCI", 1), feature("VIXCLS", 40)]
        a = audit_event_coverage(features, CHECK, EVENT)
        self.assertEqual(a["2020-crisis"]["status"], "partial_two_family_only")
        self.assertEqual(classify_misses(["2020-crisis"], a)["missed_with_partial_two_family_coverage"],
                         ["2020-crisis"])

    def test_three_independent_families_can_be_evaluated(self):
        features = [feature("NFCI", 1), feature("VIXCLS", 40), feature("BAMLH0A0HYM2", 7)]
        a = audit_event_coverage(features, CHECK, EVENT)
        self.assertEqual(a["2020-crisis"]["status"], "at_least_one_three_family_checkpoint")
        self.assertEqual(classify_misses(["2020-crisis"], a)["missed_with_three_family_coverage"],
                         ["2020-crisis"])

    def test_unpublished_hy_not_historical_coverage(self):
        features = [feature("NFCI", 1), feature("VIXCLS", 40),
                    feature("BAMLH0A0HYM2", 7, available="2020-03-17T00:00:00Z")]
        a = audit_event_coverage(features, CHECK, EVENT)
        self.assertEqual(a["2020-crisis"]["status"], "partial_two_family_only")

    def test_missing_event_checkpoint_is_not_a_miss(self):
        a = audit_event_coverage([feature("VIXCLS", 50)], [], EVENT)
        self.assertEqual(a["2020-crisis"]["checkpoints_in_window"], 0)
        self.assertEqual(a["2020-crisis"]["status"], "unassessable_no_two_family_checkpoint")

if __name__ == "__main__":
    unittest.main()
