"""Testes da v0.3: tipos de busca, método de acesso, histórico e sonar, watch, leitura de páginas,
YouTube (com respostas simuladas) e importação do Google Trends."""
import copy
import email.message
import json
import os
import tempfile
import unittest
import urllib.error
from unittest import mock

from _helpers import ROOT, example_brief, example_report
from tx import blocks, history, model, queries, render, trends, watch, webfetch, youtube

import teixugo
from test_render_cli import run


# --------------------------------------------------------------------------- modelo


class BriefKinds(unittest.TestCase):
    def test_niche_only_infers_kind(self):
        errors, _, out = model.validate_brief({"niche": "pet"})
        self.assertEqual(errors, [])
        self.assertEqual(out["kind"], "niche")
        self.assertEqual(out["scope"], "pet")

    def test_kind_niche_requires_niche(self):
        errors, _, _ = model.validate_brief({"kind": "niche", "pain": "x"})
        self.assertTrue(any("niche" in e for e in errors))

    def test_sonar_needs_some_scope(self):
        self.assertTrue(model.validate_brief({"kind": "sonar"})[0])
        self.assertEqual(model.validate_brief({"kind": "sonar", "niche": "casa"})[0], [])

    def test_invalid_kind_and_platforms(self):
        errors, _, _ = model.validate_brief({"pain": "x", "kind": "magia", "platforms": ["orkut"]})
        self.assertTrue(any("kind" in e for e in errors))
        self.assertTrue(any("platforms" in e for e in errors))

    def test_example_brief_still_valid(self):
        self.assertEqual(model.validate_brief(example_brief())[0], [])


class ReportMethods(unittest.TestCase):
    def test_example_valid_and_has_ids(self):
        r = example_report()
        self.assertEqual(model.validate_report(r), ([], []))
        self.assertTrue(all("id" in p for p in r["products"]))

    def test_unknown_method_is_error(self):
        r = example_report()
        r["products"][0]["engagement"]["method"] = "telepatia"
        errors, _ = model.validate_report(r)
        self.assertTrue(any("engagement.method" in e for e in errors))

    def test_verified_by_search_snippet_only_warns(self):
        r = example_report()
        r["products"][0]["effectiveness"]["method"] = "web_search"
        _, warnings = model.validate_report(r)
        self.assertTrue(any("trecho de busca" in w for w in warnings))

    def test_link_found_but_engagement_unverified_warns(self):
        r = example_report()
        r["products"][0]["engagement"] = {"value": "não verificado", "label": "unverified"}
        _, warnings = model.validate_report(r)
        self.assertTrue(any("maior engajamento" in w for w in warnings))

    def test_bad_and_duplicate_id(self):
        r = example_report()
        r["products"][0]["id"] = "Luva Removedora"
        r["products"][2]["id"] = r["products"][1]["id"]
        errors, _ = model.validate_report(r)
        self.assertTrue(any("kebab-case" in e for e in errors))
        self.assertTrue(any("duplicado" in e for e in errors))

    def test_niche_report_is_valid_and_titled_by_niche(self):
        r = example_report()
        del r["meta"]["pain"]
        r["meta"]["niche"] = "pet"
        r["meta"]["kind"] = "niche"
        self.assertEqual(model.validate_report(r)[0], [])
        self.assertIn("pet", blocks.build_blocks(r)[0]["text"])

    def test_report_without_pain_or_niche_fails(self):
        r = example_report()
        del r["meta"]["pain"]
        self.assertTrue(any("meta.pain ou meta.niche" in e for e in model.validate_report(r)[0]))

    def test_method_shown_in_markdown(self):
        md = render.to_md(blocks.build_blocks(example_report()))
        self.assertIn("via leitura de página", md)


# --------------------------------------------------------------------------- buscas


class QueriesV03(unittest.TestCase):
    def test_web_search_strings(self):
        rows = queries.build(example_brief(), per_term=2, limit=500)
        by_platform = {r["platform"]: r["web_search"] for r in rows if r["query"] == "remover pelo de cachorro"}
        self.assertEqual(by_platform["tiktok"], "site:tiktok.com remover pelo de cachorro")
        self.assertEqual(by_platform["mercado_livre"], "site:mercadolivre.com.br remover pelo de cachorro")
        self.assertEqual(by_platform["google"], "remover pelo de cachorro")  # sem site:
        self.assertEqual(by_platform["google_trends"], "")  # sem equivalente em busca web

    def test_instagram_is_search_only(self):
        rows = [r for r in queries.build(example_brief(), per_term=1, limit=500) if r["platform"] == "instagram"]
        self.assertTrue(rows)
        self.assertTrue(all(r["url"] == "" and r["web_search"].startswith("site:instagram.com") for r in rows))

    def test_platform_filter(self):
        b = example_brief()
        b["platforms"] = ["tiktok", "youtube"]
        rows = queries.build(b, per_term=2, limit=500)
        self.assertEqual({r["platform"] for r in rows}, {"tiktok", "youtube"})

    def test_niche_scope_without_terms(self):
        _, _, b = model.validate_brief({"niche": "organização de casa"})
        rows = queries.build(b, per_term=1, limit=500)
        self.assertTrue(rows)
        self.assertTrue(any("organização de casa" in r["query"] for r in rows))

    def test_searches_list_is_unique_and_non_empty(self):
        s = queries.to_searches(queries.build(example_brief(), per_term=3, limit=500))
        self.assertEqual(len(s), len(set(s)))
        self.assertNotIn("", s)


# --------------------------------------------------------------------------- histórico e sonar


def public_dns(host, port, type=None, **kw):
    return [(2, 1, 6, "", ("93.184.216.34", port))]


def snap(day, products):
    return {"taken_at": day, "scope": "x", "market": ["BR"],
            "products": {k: {"name": k.upper(), "solution_type": "t", "signals": v} for k, v in products.items()}}


class Growth(unittest.TestCase):
    def test_weekly_growth_math(self):
        self.assertEqual(history.weekly_growth(1000, 2000, 7, 1), 100.0)
        self.assertEqual(history.weekly_growth(1000, 1210, 14, 1), 10.0)  # 1,1 por semana
        self.assertEqual(history.weekly_growth(1000, 0, 7, 1), -100.0)

    def test_unsafe_measurements_return_none(self):
        self.assertIsNone(history.weekly_growth(500, 5000, 7, 1000))  # base pequena
        self.assertIsNone(history.weekly_growth(1000, 2000, 1, 1))  # intervalo curto
        self.assertIsNone(history.weekly_growth(None, 2000, 7, 1))
        self.assertIsNone(history.weekly_growth(0, 10, 7, 0))  # sem divisão por zero


class Compare(unittest.TestCase):
    def setUp(self):
        self.prev = snap("2026-10-01", {
            "a": {"engagement": 10000, "search_index": 40, "reviews": 100, "advertisers": 10},
            "b": {"engagement": 50000, "search_index": 60, "reviews": 900, "advertisers": 30},
            "d": {"engagement": 20000},
        })
        self.cur = snap("2026-10-08", {
            "a": {"engagement": 30000, "search_index": 80, "reviews": 150, "advertisers": 20},
            "b": {"engagement": 50000, "search_index": 60, "reviews": 900, "advertisers": 30},
            "c": {"engagement": 9000, "advertisers": 1},
        })

    def test_baseline_when_no_previous(self):
        c = history.compare(None, self.cur)
        self.assertTrue(c["baseline"])
        self.assertFalse(history.has_alert(c))
        self.assertTrue(all(i["level"] == "baseline" for i in c["items"].values()))

    def test_acceleration_levels_and_score(self):
        c = history.compare(self.prev, self.cur)
        a, b = c["items"]["a"], c["items"]["b"]
        self.assertEqual(c["days"], 7)
        self.assertEqual(a["growth"], {"social": 200.0, "search": 100.0, "reviews": 50.0, "ads": 100.0, "creators": None})
        self.assertEqual(a["acceleration"], 90.0)  # 40*1 + 30*1 + 20*0.5 + 10*1
        self.assertEqual(a["level"], "strong")
        self.assertEqual(b["acceleration"], 0.0)
        self.assertEqual(b["level"], "none")

    def test_new_and_gone(self):
        c = history.compare(self.prev, self.cur)
        self.assertEqual([n["key"] for n in c["new"]], ["c"])
        self.assertEqual([g["key"] for g in c["gone"]], ["d"])

    def test_alert_rules(self):
        c = history.compare(self.prev, self.cur)
        self.assertTrue(history.has_alert(c))
        quiet_prev = copy.deepcopy(self.prev)
        quiet_cur = copy.deepcopy(self.prev)
        quiet_cur["taken_at"] = "2026-10-08"
        quiet = history.compare(quiet_prev, quiet_cur)
        self.assertFalse(history.has_alert(quiet))
        quiet_cur["products"]["novo"] = {"name": "NOVO", "solution_type": "t", "signals": {}}
        self.assertTrue(history.has_alert(history.compare(quiet_prev, quiet_cur)))
        self.assertFalse(history.has_alert(history.compare(quiet_prev, quiet_cur, {"alert_on_new": False})))

    def test_moderate_needs_one_accelerating_component_and_does_not_alert_by_default(self):
        prev = snap("2026-10-01", {"a": {"engagement": 10000, "search_index": 50}})
        cur = snap("2026-10-08", {"a": {"engagement": 13000, "search_index": 50}})  # +30% só em engajamento
        comp = history.compare(prev, cur)
        item = comp["items"]["a"]
        self.assertEqual(item["accelerating"], ["social"])
        self.assertEqual(item["level"], "moderate")
        self.assertFalse(history.has_alert(comp))  # moderado é informativo por padrão
        self.assertTrue(history.has_alert(history.compare(prev, cur, {"alert_on_moderate": True})))

    def test_two_components_but_low_score_is_only_moderate(self):
        prev = snap("2026-10-01", {"a": {"engagement": 10000, "search_index": 50}})
        cur = snap("2026-10-08", {"a": {"engagement": 12500, "search_index": 63}})  # +25% e +26%
        item = history.compare(prev, cur, {"min_score": 40})["items"]["a"]
        self.assertEqual(item["accelerating"], ["social", "search"])
        self.assertEqual(item["level"], "moderate")  # nota ~25,5 < 40
        strong = history.compare(prev, cur, {"min_score": 20})["items"]["a"]
        self.assertEqual(strong["level"], "strong")

    def test_window_scores_reward_attention_with_few_advertisers(self):
        w = history.window_scores({
            "hot": {"engagement": 1000000, "advertisers": 2},
            "crowded": {"engagement": 1000000, "advertisers": 50},
            "nodata": {"engagement": 5},
        })
        self.assertGreater(w["hot"], w["crowded"])
        self.assertIsNone(w["nodata"])

    def test_same_day_snapshot_replaces_and_previous_picks_latest_older(self):
        h = {"snapshots": []}
        history.add_snapshot(h, snap("2026-10-01", {"a": {}}))
        history.add_snapshot(h, snap("2026-10-08", {"a": {}}))
        history.add_snapshot(h, snap("2026-10-08", {"a": {}, "b": {}}))
        self.assertEqual(len(h["snapshots"]), 2)
        self.assertEqual(history.previous(h, "2026-10-15")["taken_at"], "2026-10-08")
        self.assertIsNone(history.previous(h, "2026-10-01"))


# --------------------------------------------------------------------------- watch


def report_on(day, bump=1.0, kind="sonar"):
    r = example_report()
    r["meta"]["generated_at"] = day
    r["meta"]["kind"] = kind
    r["meta"].pop("demo", None)
    for p in r["products"]:
        sig = p["signals"]
        sig["engagement"] = int(sig["engagement"] * bump)
        sig["search_index"] = sig["search_index"] * bump
    return r


class Watch(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.store = os.path.join(self.tmp.name, "w")
        _, _, self.brief = model.validate_brief({"kind": "sonar", "pain": "remover pelo de cachorro"})

    def test_add_list_get_and_errors(self):
        watch.add(self.store, "pelo-cachorro", self.brief, channels=["email", "push"])
        self.assertIn("pelo-cachorro", watch.list_watches(self.store))
        with self.assertRaises(ValueError):
            watch.add(self.store, "pelo-cachorro", self.brief)  # duplicada
        with self.assertRaises(ValueError):
            watch.add(self.store, "ID Inválido", self.brief)
        with self.assertRaises(ValueError):
            watch.add(self.store, "outro", self.brief, channels=["pombo"])
        with self.assertRaises(KeyError):
            watch.get(self.store, "nao-existe")

    def test_baseline_then_acceleration_alert(self):
        watch.add(self.store, "w1", self.brief)
        first = watch.update(self.store, "w1", report_on("2026-10-01"))
        self.assertTrue(first["comparison"]["baseline"])
        self.assertFalse(first["alert"])
        self.assertIn("linha de base", first["digest"])

        second_report = report_on("2026-10-08", bump=2.0)
        second = watch.update(self.store, "w1", second_report)
        self.assertTrue(second["alert"])
        self.assertIn("Em aceleração", second["digest"])
        self.assertTrue(os.path.exists(second["digest_path"]))
        # o relatório recebeu sonar e radar, e a ordem segue a aceleração
        self.assertIn("sonar", second_report["products"][0])
        self.assertFalse(second_report["radar"]["baseline"])
        self.assertEqual(second_report["radar"]["compared_to"], "2026-10-01")
        # o histórico guardou as duas leituras
        with open(os.path.join(self.store, "history", "w1.json"), encoding="utf-8") as fh:
            self.assertEqual(len(json.load(fh)["snapshots"]), 2)

    def test_flat_second_reading_has_no_alert(self):
        watch.add(self.store, "w2", self.brief)
        watch.update(self.store, "w2", report_on("2026-10-01"))
        res = watch.update(self.store, "w2", report_on("2026-10-08", bump=1.0))
        self.assertFalse(res["alert"])
        self.assertIn("Nenhum produto passou", res["digest"])

    def test_english_digest(self):
        watch.add(self.store, "w3", self.brief)
        r1 = report_on("2026-10-01")
        r1["meta"]["language"] = "en"
        res = watch.update(self.store, "w3", r1)
        self.assertIn("First reading", res["digest"])

    def test_invalid_date_override(self):
        watch.add(self.store, "w4", self.brief)
        with self.assertRaises(ValueError):
            watch.update(self.store, "w4", report_on("2026-10-01"), taken_at="amanhã")

    def test_routine_prompt_mentions_essentials(self):
        entry = watch.add(self.store, "w5", self.brief, schedule="toda segunda, 8h")
        text = watch.routine_prompt("w5", entry, self.store)
        for needle in ("w5", "watch update", "código de saída for 10", "robots.txt", "toda segunda, 8h", "remover pelo de cachorro"):
            self.assertIn(needle, text)

    def test_sonar_section_in_rendered_report(self):
        watch.add(self.store, "w6", self.brief)
        watch.update(self.store, "w6", report_on("2026-10-01"))
        r = report_on("2026-10-08", bump=2.0)
        watch.update(self.store, "w6", r)
        md = render.to_md(blocks.build_blocks(r))
        self.assertIn("## Sonar", md)
        self.assertIn("Aceleração (0–100)", md)
        self.assertIn("não é previsão", md)


class WatchCLI(unittest.TestCase):
    def test_full_flow_and_exit_codes(self):
        with tempfile.TemporaryDirectory() as tmp:
            store = os.path.join(tmp, "w")
            brief = os.path.join(tmp, "brief.json")
            with open(brief, "w", encoding="utf-8") as fh:
                json.dump({"kind": "sonar", "pain": "remover pelo de cachorro"}, fh)
            self.assertEqual(run("watch", "add", "cli", brief, "--store", store, "--channels", "email,calendar")[0], 0)
            self.assertEqual(run("watch", "add", "cli", brief, "--store", store)[0], 2)  # duplicada
            self.assertIn("cli", run("watch", "list", "--store", store)[1])

            paths = []
            for day, bump in (("2026-10-01", 1.0), ("2026-10-08", 2.0)):
                path = os.path.join(tmp, f"{day}.json")
                with open(path, "w", encoding="utf-8") as fh:
                    json.dump(report_on(day, bump), fh)
                paths.append(path)
            code1, out1 = run("watch", "update", "cli", paths[0], "--store", store)
            self.assertEqual((code1, "sem alerta" in out1), (0, True))
            code2, out2 = run("watch", "update", "cli", paths[1], "--store", store)
            self.assertEqual(code2, watch.EXIT_ALERT)
            self.assertIn("ALERTA", out2)
            with open(paths[1], encoding="utf-8") as fh:  # relatório enriquecido gravado de volta
                self.assertIn("radar", json.load(fh))
            code3, out3 = run("watch", "routine", "cli", "--store", store)
            self.assertEqual(code3, 0)
            self.assertIn("watch update cli", out3)
            self.assertEqual(run("watch", "update", "nao-existe", paths[0], "--store", store)[0], 2)

    def test_queries_searches_format(self):
        code, out = run("queries", os.path.join(ROOT, "examples", "brief.example.json"), "--format", "searches", "--limit", "30")
        self.assertEqual(code, 0)
        self.assertIn("site:tiktok.com remover pelo de cachorro", out.splitlines())


# --------------------------------------------------------------------------- leitura de páginas


class FakeResp:
    def __init__(self, body, status=200, url="https://loja.test/p/1"):
        self._b = body.encode("utf-8")
        self.status = status
        self._url = url
        self.headers = email.message.Message()
        self.headers["Content-Type"] = "text/html; charset=utf-8"

    def read(self, n=-1):
        return self._b if n is None or n < 0 else self._b[:n]

    def geturl(self):
        return self._url


def make_opener(pages, robots=None, robots_error=None):
    """pages: {url: corpo | HTTPError code}. robots: texto do robots.txt."""
    def opener(req, timeout):
        url = req.full_url
        if url.endswith("/robots.txt"):
            if robots_error:
                raise robots_error
            if robots is None:
                raise urllib.error.HTTPError(url, 404, "nf", {}, None)
            return FakeResp(robots, url=url)
        body = pages.get(url)
        if isinstance(body, int):
            raise urllib.error.HTTPError(url, body, "x", {}, None)
        return FakeResp(body, url=url)
    return opener


PRODUCT_HTML = """<html><head><title> Luva  Pet </title>
<meta name="description" content="Tira pelos">
<meta property="og:title" content="Luva Pet OG">
<link rel="canonical" href="https://loja.test/p/1">
<script type="application/ld+json">{"@context":"https://schema.org","@graph":[{"@type":"WebPage"},
{"@type":"Product","name":"Luva Pet","brand":{"@type":"Brand","name":"Acme"},
"offers":{"@type":"Offer","price":"19.90","priceCurrency":"BRL"},
"aggregateRating":{"@type":"AggregateRating","ratingValue":"4.6","reviewCount":"591"}}]}</script>
</head><body><h1>Luva Pet</h1></body></html>"""


class WebFetch(unittest.TestCase):
    URL = "https://loja.test/p/1"

    def setUp(self):
        # sem DNS de verdade: todo nome resolve para um IP público fixo
        patcher = mock.patch("tx.netguard.socket.getaddrinfo", side_effect=public_dns)
        patcher.start()
        self.addCleanup(patcher.stop)

    def test_extracts_title_description_and_jsonld_product(self):
        res = webfetch.fetch(self.URL, opener=make_opener({self.URL: PRODUCT_HTML}))
        self.assertIsNone(res["error"])
        self.assertEqual(res["title"], "Luva Pet")
        self.assertEqual(res["description"], "Tira pelos")
        self.assertEqual(res["h1"], "Luva Pet")
        self.assertEqual(res["canonical"], "https://loja.test/p/1")
        self.assertEqual(res["og"]["title"], "Luva Pet OG")
        self.assertEqual(res["product"], {"name": "Luva Pet", "brand": "Acme", "price": "19.90", "currency": "BRL", "rating": "4.6", "reviews": "591"})
        self.assertEqual(res["robots"], "allowed")

    def test_refuses_when_robots_disallows_ai_agents(self):
        robots = "User-agent: Claude-User\nDisallow: /\n\nUser-agent: *\nAllow: /\n"
        opener = make_opener({self.URL: PRODUCT_HTML}, robots=robots)
        res = webfetch.fetch(self.URL, opener=opener)
        self.assertEqual(res["robots"], "blocked")
        self.assertIn("Claude-User", res["error"])
        self.assertIsNone(res["status"])  # nem chegou a pedir a página

    def test_refuses_when_robots_disallows_us(self):
        robots = "User-agent: *\nDisallow: /p/\n"
        res = webfetch.fetch(self.URL, opener=make_opener({self.URL: PRODUCT_HTML}, robots=robots))
        self.assertEqual(res["robots"], "blocked")

    def test_missing_robots_means_allowed_and_robots_outage_is_unknown(self):
        ok = webfetch.fetch(self.URL, opener=make_opener({self.URL: PRODUCT_HTML}))
        self.assertEqual(ok["robots"], "allowed")
        down = webfetch.fetch(self.URL, opener=make_opener({self.URL: PRODUCT_HTML}, robots_error=OSError("sem rede")))
        self.assertEqual(down["robots"], "unknown")
        self.assertIsNone(down["error"])

    def test_http_block_is_reported_not_bypassed(self):
        res = webfetch.fetch(self.URL, opener=make_opener({self.URL: 403}))
        self.assertEqual(res["status"], 403)
        self.assertIn("não contorne", res["error"])

    def test_javascript_shell_is_flagged(self):
        res = webfetch.fetch(self.URL, opener=make_opener({self.URL: "<html><body><div id='root'></div></body></html>"}))
        self.assertIn("JavaScript", res["error"])

    def test_rejects_non_http_scheme(self):
        for bad in ("file:///etc/passwd", "ftp://x.test/a", "javascript:alert(1)", "loja.test/p"):
            self.assertIsNotNone(webfetch.fetch(bad, opener=make_opener({}))["error"], bad)

    def test_product_extraction_handles_lists_and_garbage(self):
        self.assertIsNone(webfetch.extract_product(["{não é json"]))
        ld = '[{"@type":["Thing","Product"],"name":"X","offers":[{"price":"1"}]}]'
        self.assertEqual(webfetch.extract_product([ld])["price"], "1")

    def test_cli_invalid_scheme_exit_1(self):
        code, out = run("fetch", "ftp://x.test/a")
        self.assertEqual(code, 1)
        self.assertIn("esquema", out)


# --------------------------------------------------------------------------- YouTube


class YouTube(unittest.TestCase):
    def fake_get(self, url, timeout):
        if "/search?" in url:
            return {"items": [{"id": {"videoId": "v1"}}, {"id": {"videoId": "v2"}}, {"id": {}}]}
        return {"items": [
            {"id": "v1", "snippet": {"title": "A", "channelTitle": "C1", "publishedAt": "2026-09-01T00:00:00Z"},
             "statistics": {"viewCount": "1500", "likeCount": "90", "commentCount": "7"}},
            {"id": "v2", "snippet": {"title": "B", "channelTitle": "C2", "publishedAt": "2026-09-02T00:00:00Z"},
             "statistics": {"viewCount": "250000", "likeCount": "9000"}},  # comentários desligados
        ]}

    def test_sorted_by_views_with_hidden_stats_as_none(self):
        v = youtube.search_videos("luva", "KEY", get_json=self.fake_get)
        self.assertEqual([x["video_id"] for x in v], ["v2", "v1"])
        self.assertEqual(v[0]["url"], "https://www.youtube.com/watch?v=v2")
        self.assertIsNone(v[0]["comments"])

    def test_evidence_is_verified_api_with_url(self):
        ev = youtube.as_evidence(youtube.search_videos("luva", "KEY", get_json=self.fake_get), today="2026-10-05")
        self.assertEqual(ev["top_post"]["value"], "https://www.youtube.com/watch?v=v2")
        self.assertEqual((ev["top_post"]["label"], ev["top_post"]["method"]), ("verified", "api"))
        self.assertIn("250.000 views", ev["engagement"]["value"])
        self.assertEqual(ev["signals"]["engagement"], 250000)
        # os campos gerados passam na validação do relatório
        errors, warnings = [], []
        model._check_field("p.top_post", ev["top_post"], "live", errors, warnings, url_value=True)
        model._check_field("p.engagement", ev["engagement"], "live", errors, warnings)
        self.assertEqual((errors, warnings), ([], []))

    def test_no_results_and_missing_key(self):
        self.assertEqual(youtube.search_videos("x", "K", get_json=lambda u, t: {"items": []}), [])
        self.assertIsNone(youtube.as_evidence([]))
        with self.assertRaises(youtube.YouTubeError):
            youtube.search_videos("x", "")

    def test_cli_without_key_fails_cleanly(self):
        old = os.environ.pop("YOUTUBE_API_KEY", None)
        try:
            code, out = run("youtube", "luva")
        finally:
            if old is not None:
                os.environ["YOUTUBE_API_KEY"] = old
        self.assertEqual(code, 2)
        self.assertIn("YOUTUBE_API_KEY", out)

    def test_key_is_never_in_error_message(self):
        def boom(url, timeout):
            raise youtube.YouTubeError("YouTube API respondeu HTTP 403. quotaExceeded")
        with self.assertRaises(youtube.YouTubeError) as ctx:
            youtube.search_videos("x", "SEGREDO123", get_json=boom)
        self.assertNotIn("SEGREDO123", str(ctx.exception))


# --------------------------------------------------------------------------- Google Trends CSV

TRENDS_CSV = """Categoria: Todas as categorias

Semana,luva removedora de pelo: (Brasil),rolo adesivo: (Brasil)
2026-01-04,10,50
2026-01-11,20,<1
2026-01-18,30,40
2026-01-25,60,45
2026-02-01,80,50
2026-02-08,100,55
"""


class TrendsImport(unittest.TestCase):
    def test_parse_means_peak_and_change(self):
        res = trends.parse(TRENDS_CSV)
        a, b = res["terms"]
        self.assertEqual(a["term"], "luva removedora de pelo")
        self.assertEqual((a["points"], a["mean"], a["peak"], a["peak_date"]), (6, 50.0, 100.0, "2026-02-08"))
        self.assertEqual(a["recent"], 90.0)  # média do último terço (80 e 100)
        self.assertEqual(a["change_pct"], 500.0)  # (90-15)/15
        self.assertEqual(b["mean"], round((50 + 0.5 + 40 + 45 + 50 + 55) / 6, 1))  # "<1" vira 0,5
        self.assertEqual(res["period"], ["2026-01-04", "2026-02-08"])

    def test_unrecognised_file_raises(self):
        with self.assertRaises(ValueError):
            trends.parse("isto não é um export do trends")

    def test_cli(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = os.path.join(tmp, "t.csv")
            with open(path, "w", encoding="utf-8") as fh:
                fh.write(TRENDS_CSV)
            code, out = run("trends-import", path)
            self.assertEqual(code, 0)
            self.assertEqual(json.loads(out)["terms"][0]["peak"], 100.0)
            self.assertEqual(run("trends-import", os.path.join(tmp, "nao-existe.csv"))[0], 2)


if __name__ == "__main__":
    unittest.main()
