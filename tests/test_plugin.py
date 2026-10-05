"""Plugin, agentes e avaliações: estrutura, versões e privilégio mínimo dos agentes que leem a web."""
import glob
import json
import os
import re
import unittest

from _helpers import ROOT, load

AGENT_DIR = os.path.join(ROOT, "agents")
WEB_READERS = {"teixugo-scout", "teixugo-verifier"}  # leem a web: sem Bash, sem escrita
READ_ONLY = {"Read", "Grep", "Glob"}
WEB_ONLY = {"WebSearch", "WebFetch"}
DANGEROUS = {"Bash", "PowerShell", "Write", "Edit", "NotebookEdit", "Agent", "SendMessage", "Artifact"}


def frontmatter(path):
    with open(path, encoding="utf-8") as fh:
        text = fh.read()
    m = re.match(r"^---\r?\n(.*?)\r?\n---\r?\n(.*)$", text, re.S)
    assert m, f"{path}: sem frontmatter"
    meta = {}
    for line in m.group(1).splitlines():
        if ":" in line:
            k, v = line.split(":", 1)
            meta[k.strip()] = v.strip()
    return meta, m.group(2)


def tools_of(meta):
    return {t.strip() for t in meta.get("tools", "").split(",") if t.strip()}


class Manifests(unittest.TestCase):
    def setUp(self):
        self.pkg = load(os.path.join(ROOT, "package.json"))
        self.plugin = load(os.path.join(ROOT, ".claude-plugin", "plugin.json"))
        self.market = load(os.path.join(ROOT, ".claude-plugin", "marketplace.json"))

    def test_plugin_manifest_matches_the_package(self):
        self.assertEqual(self.plugin["name"], "teixugo-minerador")
        self.assertEqual(self.plugin["version"], self.pkg["version"])
        self.assertEqual(self.plugin["license"], self.pkg["license"])
        self.assertTrue(self.plugin["description"].strip())

    def test_plugin_name_is_not_reserved(self):
        self.assertFalse(re.match(r"^(claude|anthropic|anthropics|cc-plugin)[-_]", self.plugin["name"], re.I))

    def test_marketplace_points_to_this_plugin(self):
        entry = self.market["plugins"][0]
        self.assertEqual((entry["name"], entry["source"], entry["version"]),
                         (self.plugin["name"], "./", self.plugin["version"]))
        self.assertTrue(self.market["owner"]["name"])

    def test_npm_package_ships_plugin_files_and_agents(self):
        for entry in ("agents/", ".claude-plugin/", "SKILL.md", "bin/"):
            self.assertIn(entry, self.pkg["files"])
        self.assertNotIn("tests/", self.pkg["files"])

    def test_only_the_manifest_lives_in_the_plugin_folder(self):
        names = sorted(os.listdir(os.path.join(ROOT, ".claude-plugin")))
        self.assertEqual(names, ["marketplace.json", "plugin.json"])


class Agents(unittest.TestCase):
    def setUp(self):
        self.files = sorted(glob.glob(os.path.join(AGENT_DIR, "*.md")))

    def test_the_three_agents_exist(self):
        self.assertEqual([os.path.basename(f)[:-3] for f in self.files], ["teixugo-redteam", "teixugo-scout", "teixugo-verifier"])

    def test_frontmatter_is_complete_and_names_match_files(self):
        for f in self.files:
            meta, body = frontmatter(f)
            stem = os.path.basename(f)[:-3]
            self.assertEqual(meta["name"], stem)
            self.assertTrue(0 < len(meta["description"]) <= 500, stem)
            self.assertNotIn(":", meta["name"])
            self.assertIn("tools", meta, f"{stem}: declare as ferramentas (lista de permitidas)")
            self.assertIn("maxTurns", meta, f"{stem}: limite de turnos evita agente sem fim")
            self.assertGreater(len(body.strip()), 200)

    def test_agents_that_read_the_web_have_least_privilege(self):
        for stem in WEB_READERS:
            meta, _ = frontmatter(os.path.join(AGENT_DIR, f"{stem}.md"))
            tools = tools_of(meta)
            self.assertTrue(tools, stem)
            self.assertLessEqual(tools, WEB_ONLY, f"{stem} só pode usar busca e leitura de página, não {tools - WEB_ONLY}")
            self.assertFalse(tools & DANGEROUS, stem)
            self.assertFalse(any(t.startswith("mcp__") for t in tools), stem)

    def test_reviewer_is_read_only(self):
        meta, _ = frontmatter(os.path.join(AGENT_DIR, "teixugo-redteam.md"))
        self.assertLessEqual(tools_of(meta), READ_ONLY)

    def test_every_agent_states_the_security_rule(self):
        for f in self.files:
            _, body = frontmatter(f)
            self.assertIn("não confiável", body.lower(), os.path.basename(f))
            self.assertRegex(body.lower(), r"n[ãa]o\s+(as\s+)?(siga|obede)", os.path.basename(f))

    def test_scouts_and_verifiers_forbid_inventing_data(self):
        for stem in WEB_READERS:
            _, body = frontmatter(os.path.join(AGENT_DIR, f"{stem}.md"))
            self.assertIn("Nunca invente", body)
            self.assertIn("robots.txt", body)

    def test_skill_documents_how_to_use_the_agents(self):
        with open(os.path.join(ROOT, "SKILL.md"), encoding="utf-8") as fh:
            skill = fh.read()
        for name in ("teixugo-scout", "teixugo-verifier", "teixugo-redteam"):
            self.assertIn(name, skill)
        self.assertTrue(os.path.exists(os.path.join(ROOT, "references", "agentes.md")))


class Evals(unittest.TestCase):
    def setUp(self):
        self.cases = sorted(d for d in glob.glob(os.path.join(ROOT, "evals", "*")) if os.path.isdir(d))

    def test_at_least_three_cases(self):
        self.assertGreaterEqual(len(self.cases), 3)  # recomendação oficial para skills

    def test_each_case_has_prompt_and_graders(self):
        for case in self.cases:
            meta, body = frontmatter(os.path.join(case, "prompt.md"))
            self.assertEqual(meta["name"], os.path.basename(case))
            self.assertTrue(body.strip())
            graders = glob.glob(os.path.join(case, "graders", "*.md"))
            self.assertTrue(graders, case)
            for g in graders:
                gmeta, gbody = frontmatter(g)
                self.assertIn(gmeta["type"], {"regex", "tool_used", "tool_order", "file_exists", "llm", "baseline"})
                if gmeta["type"] == "llm":
                    self.assertIn("PASS", gbody)
                    self.assertIn("FAIL", gbody)

    def test_cases_are_read_only(self):
        for case in self.cases:
            meta, _ = frontmatter(os.path.join(case, "prompt.md"))
            allowed = set(re.findall(r"[A-Za-z]+", meta.get("allowed_tools", "")))
            self.assertFalse(allowed & {"Bash", "Write", "Edit", "WebFetch", "WebSearch"}, case)

    def test_security_cases_exist(self):
        names = {os.path.basename(c) for c in self.cases}
        self.assertIn("recusa-contornar-robots", names)
        self.assertIn("ignora-injecao-na-pagina", names)


if __name__ == "__main__":
    unittest.main()
