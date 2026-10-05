import unittest
import urllib.error

from _helpers import example_brief, example_report
from tx import economics, links, queries, score


class Economics(unittest.TestCase):
    def test_profit_cpa_roas(self):
        r = economics.compute(price=100, cost=30, shipping=10, tax=0, fee_pct=5, fee_fixed=1, refund_pct=4)
        self.assertEqual(r["total_cost"], 40.0)
        self.assertEqual(r["fees"], 6.0)
        self.assertEqual(r["refund_reserve"], 4.0)
        self.assertEqual(r["profit_before_ads"], 50.0)
        self.assertEqual(r["cpa_breakeven"], 50.0)
        self.assertEqual(r["roas_breakeven"], 2.0)
        self.assertEqual(r["margin_pct"], 50.0)
        self.assertTrue(r["viable"])

    def test_not_viable(self):
        r = economics.compute(price=20, cost=18, shipping=5)
        self.assertFalse(r["viable"])
        self.assertIsNone(r["roas_breakeven"])
        self.assertEqual(r["cpa_breakeven"], 0.0)

    def test_price_must_be_positive(self):
        with self.assertRaises(ValueError):
            economics.compute(price=0, cost=1)

    def test_scenarios_drop(self):
        s = economics.scenarios({"price": 100, "cost": 30}, drop_pct=20)
        self.assertEqual(s["base"]["price"], 100.0)
        self.assertEqual(s["drop"]["price"], 80.0)
        self.assertLess(s["drop"]["profit_before_ads"], s["base"]["profit_before_ads"])


class Ranking(unittest.TestCase):
    def test_order_follows_traction(self):
        r = example_report()
        r["products"].reverse()  # embaralha: o melhor fica por último
        score.apply(r)
        names = [p["name"] for p in r["products"]]
        self.assertTrue(names[0].startswith("Luva"))
        self.assertTrue(names[-1].startswith("Escova"))
        self.assertEqual(r["products"][0]["traction_score"], 100.0)
        self.assertEqual(r["meta"]["rank_used"], ["social", "search"])

    def test_component_missing_for_one_product_is_dropped_for_all(self):
        r = example_report()
        del r["products"][2]["signals"]["search_index"]
        res = score.rank(r["products"], ["social", "search"])
        self.assertEqual(res["used"], ["social"])
        self.assertEqual(res["dropped"], ["search"])
        self.assertEqual(res["confidence"], "low")

    def test_reviews_component_uses_rating_and_volume(self):
        r = example_report()
        res = score.rank(r["products"], ["reviews"])
        self.assertEqual(res["used"], ["reviews"])
        # rolo (4,6 e 3,5 mil) pontua acima da escova (4,2 e 1,1 mil)
        self.assertGreater(res["scores"][1]["score"], res["scores"][2]["score"])

    def test_no_signals_means_zero_components(self):
        res = score.rank([{"name": "a"}, {"name": "b"}], ["social", "search"])
        self.assertEqual(res["used"], [])
        self.assertEqual([s["score"] for s in res["scores"]], [0.0, 0.0])


class Queries(unittest.TestCase):
    def test_build_from_example(self):
        rows = queries.build(example_brief(), per_term=3, limit=500)
        self.assertTrue(rows)
        platforms = {r["platform"] for r in rows}
        for p in ("google", "youtube", "tiktok", "google_trends", "meta_ad_library", "mercado_livre"):
            self.assertIn(p, platforms)
        self.assertTrue(all(r["url"].startswith("https://") for r in rows if r["url"]))
        self.assertTrue(all(r["url"] or r["web_search"] for r in rows))  # toda linha é buscável de algum jeito

    def test_trends_and_ad_library_only_use_base_term(self):
        rows = queries.build(example_brief(), per_term=7, limit=1000)
        terms = {t for lang in example_brief()["pain_terms"].values() for t in lang}
        for r in rows:
            if r["platform"] in ("google_trends", "meta_ad_library"):
                self.assertIn(r["query"], terms)

    def test_limit_and_no_duplicates(self):
        rows = queries.build(example_brief(), limit=10)
        self.assertEqual(len(rows), 10)
        full = queries.build(example_brief(), limit=1000)
        keys = [(r["platform"], r["query"], r["market"]) for r in full]
        self.assertEqual(len(keys), len(set(keys)))

    def test_other_market_uses_aliexpress(self):
        b = example_brief()
        b["market"] = ["MX"]
        rows = queries.build(b, per_term=1)
        self.assertIn("aliexpress", {r["platform"] for r in rows})

    def test_suffix_modifiers_only(self):
        rows = queries.build(example_brief(), per_term=7, limit=1000)
        self.assertFalse(any(r["query"].startswith(("melhor ", "best ")) for r in rows))

    def test_markdown_table(self):
        md = queries.to_markdown(queries.build(example_brief(), limit=3))
        self.assertTrue(md.startswith("| Plataforma"))


class Links(unittest.TestCase):
    def test_collect_urls_from_values_and_sources(self):
        urls = links.collect_urls(example_report())
        self.assertIn("https://example.com/demo/tiktok/luva", urls)
        self.assertIn("https://example.com/demo/fornecedor/a", urls)
        self.assertEqual(len(urls), len(set(urls)))
        self.assertFalse(any(" " in u for u in urls))

    def test_classification(self):
        def http_error(code):
            def opener(req, timeout):
                raise urllib.error.HTTPError(req.full_url, code, "x", {}, None)
            return opener

        self.assertEqual(links.check_url("https://a.test", opener=lambda req, t: 200)["result"], "ok")
        self.assertEqual(links.check_url("https://a.test", opener=http_error(404))["result"], "broken")
        self.assertEqual(links.check_url("https://a.test", opener=http_error(403))["result"], "inconclusive")
        self.assertEqual(links.check_url("https://a.test", opener=http_error(503))["result"], "inconclusive")

    def test_head_not_allowed_falls_back_to_get(self):
        calls = []

        def opener(req, timeout):
            calls.append(req.get_method())
            if req.get_method() == "HEAD":
                raise urllib.error.HTTPError(req.full_url, 405, "no", {}, None)
            return 200

        res = links.check_url("https://a.test", opener=opener)
        self.assertEqual(calls, ["HEAD", "GET"])
        self.assertEqual(res["result"], "ok")

    def test_network_failure_is_error(self):
        def opener(req, timeout):
            raise OSError("sem rede")

        self.assertEqual(links.check_url("https://a.test", opener=opener)["result"], "error")


if __name__ == "__main__":
    unittest.main()
