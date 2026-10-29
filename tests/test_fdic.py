"""Official FDIC failure feed: no source rumor, no double review, no crisis auto-alert."""
import json
import tempfile
import unittest
from pathlib import Path
from datetime import datetime,timezone
from fcews.fdic import parse_failures,refresh,file_review_issues

NOW=datetime(2026,10,29,1,0,tzinfo=timezone.utc)
SAMPLE={
    "data":[
        {"data":{"CERT":24735,"NAME":"SILICON VALLEY BANK",
                 "FAILDATE":"2023-03-10","QBFASSET":209026000}},
        {"data":{"CERT":99887,"NAME":"HYPOTHETICAL BANK",
                 "FAILDATE":"2026-10-28","QBFASSET":30000000}},
        {"data":{"CERT":99888,"NAME":"TINY COMMUNITY BANK",
                 "FAILDATE":"2026-10-28","QBFASSET":100000}},
    ]
}

class Client:
    def __init__(self):
        self.issues={}
    def find_body_fingerprint(self,key):
        return next((i for i in self.issues.values() if "FCEWS-FP:"+key in i["body"]),None)
    def create(self,title,body):
        i={"number":len(self.issues)+1,"title":title,"body":body,
           "html_url":"https://github.com/repo/issues/"+str(len(self.issues)+1)}
        self.issues[i["number"]]=i
        return i
    def get(self,number):
        return self.issues[number]

class FDICIntakeTests(unittest.TestCase):
    def test_fdic_assets_are_thousands_of_usd(self):
        items=parse_failures(json.dumps(SAMPLE))
        svb=next(x for x in items if x["cert"]=="24735")
        self.assertEqual(svb["assets_usd_m"],209026)
        self.assertFalse(svb["is_crisis_alert"])

    def test_first_poll_queues_only_new_large_recent_case(self):
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp)
            one=refresh(root,NOW,lambda url,timeout:json.dumps(SAMPLE))
            self.assertEqual(len(one["new_review_queue"]),1)
            self.assertEqual(one["new_review_queue"][0]["cert"],"99887")
            self.assertEqual(one["new_review_queue"][0]["review_status"],"pending_primary_document")
            gh=Client()
            r=file_review_issues(root,gh)
            self.assertEqual(r["count"],1)
            self.assertEqual(r["financial_alerts"],0)
            self.assertIn("REVIEW ONLY",next(iter(gh.issues.values()))["title"])
            self.assertEqual(file_review_issues(root,gh)["count"],0)
            self.assertEqual(len(gh.issues),1)
            two=refresh(root,NOW,lambda url,timeout:json.dumps(SAMPLE))
            self.assertEqual(two["new_review_queue"],[])

    def test_lost_post_ack_still_replays_pending_review(self):
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp)
            refresh(root,NOW,lambda url,timeout:json.dumps(SAMPLE))
            gh=Client()
            original=gh.create
            def lost_ack(title,body):
                original(title,body)
                raise TimeoutError("GitHub response lost")
            gh.create=lost_ack
            with self.assertRaises(TimeoutError):
                file_review_issues(root,gh)
            self.assertEqual(len(gh.issues),1)
            gh.create=original
            result=file_review_issues(root,gh)
            self.assertEqual(result["count"],1)
            self.assertEqual(len(gh.issues),1)
            state=json.loads((root/"data/fdic_review.json").read_text())
            self.assertEqual(state["pending_review"],[])

    def test_source_outage_preserves_known_events(self):
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp)
            refresh(root,NOW,lambda url,timeout:json.dumps(SAMPLE))
            two=refresh(root,NOW,lambda url,timeout:(_ for _ in ()).throw(TimeoutError("no")))
            self.assertEqual(two["status"],"error")
            self.assertTrue(two["known_event_ids"])

    def test_html_fails_cleanly(self):
        with self.assertRaises(ValueError):
            parse_failures("<html>denied</html>")

if __name__=="__main__":
    unittest.main()
