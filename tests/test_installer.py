"""Testes do instalador (bin/install.js). Pulados quando o Node não está instalado."""
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
import unittest

from _helpers import ROOT

NODE = shutil.which("node")
INSTALL = os.path.join(ROOT, "bin", "install.js")
SKILL = "teixugo-minerador"


def run_installer(*args, cwd=None):
    r = subprocess.run(
        [NODE, INSTALL, "--lang", "pt", *args], cwd=cwd, capture_output=True, text=True, encoding="utf-8", timeout=60
    )
    return r.returncode, r.stdout + r.stderr


@unittest.skipUnless(NODE, "Node.js não encontrado")
class Installer(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.dest = os.path.join(self.tmp.name, "skills")
        self.target = os.path.join(self.dest, SKILL)

    def install(self, *extra):
        return run_installer("--dest", self.dest, *extra)

    def test_fresh_install_copies_only_the_skill(self):
        code, out = self.install()
        self.assertEqual(code, 0, out)
        for rel in ("SKILL.md", "scripts/teixugo.py", "scripts/tx/model.py", "references/briefing.md",
                    "examples/report.example.pt-BR.json", "LICENSE", ".installed-version"):
            self.assertTrue(os.path.exists(os.path.join(self.target, rel)), rel)
        for rel in ("tests", ".github", "bin", "package.json", ".git"):
            self.assertFalse(os.path.exists(os.path.join(self.target, rel)), f"não deveria copiar {rel}")
        for dirpath, dirnames, _ in os.walk(self.target):
            self.assertNotIn("__pycache__", dirnames)

    def test_installed_copy_runs_on_its_own(self):
        self.install()
        script = os.path.join(self.target, "scripts", "teixugo.py")
        example = os.path.join(self.target, "examples", "report.example.pt-BR.json")
        r = subprocess.run([sys.executable, script, "validate", example], capture_output=True, text=True, encoding="utf-8")
        self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
        r = subprocess.run([sys.executable, script, "doctor"], capture_output=True, text=True, encoding="utf-8")
        self.assertEqual(r.returncode, 0)

    def test_update_replaces_skill_files_and_keeps_user_data(self):
        self.install()
        os.makedirs(os.path.join(self.target, "teixugo-relatorios"))
        os.makedirs(os.path.join(self.target, "teixugo-watch", "history"))
        with open(os.path.join(self.target, "teixugo-relatorios", "meu.md"), "w", encoding="utf-8") as fh:
            fh.write("meu relatório")
        with open(os.path.join(self.target, "teixugo-watch", "history", "w.json"), "w", encoding="utf-8") as fh:
            fh.write("{}")
        stale = os.path.join(self.target, "references", "arquivo-antigo.md")
        with open(stale, "w", encoding="utf-8") as fh:
            fh.write("sobrou de uma versão anterior")
        with open(os.path.join(self.target, "SKILL.md"), "a", encoding="utf-8") as fh:
            fh.write("\nedição local\n")

        code, out = self.install()
        self.assertEqual(code, 0, out)
        self.assertIn("Atualizando", out)
        self.assertFalse(os.path.exists(stale), "arquivo que a versão nova não tem deveria sumir")
        with open(os.path.join(self.target, "SKILL.md"), encoding="utf-8") as fh:
            self.assertNotIn("edição local", fh.read())
        self.assertTrue(os.path.exists(os.path.join(self.target, "teixugo-relatorios", "meu.md")))
        self.assertTrue(os.path.exists(os.path.join(self.target, "teixugo-watch", "history", "w.json")))

    def test_refuses_foreign_folder_unless_forced(self):
        os.makedirs(self.target)
        mine = os.path.join(self.target, "SKILL.md")
        with open(mine, "w", encoding="utf-8") as fh:
            fh.write("---\nname: outra-skill\ndescription: x\n---\n")
        code, out = self.install()
        self.assertEqual(code, 1)
        self.assertIn("não parece ser desta skill", out)
        with open(mine, encoding="utf-8") as fh:
            self.assertIn("outra-skill", fh.read())  # intacto
        code, _ = self.install("--force")
        self.assertEqual(code, 0)
        with open(mine, encoding="utf-8") as fh:
            self.assertIn(f"name: {SKILL}", fh.read())

    def test_dry_run_changes_nothing(self):
        code, out = self.install("--dry-run")
        self.assertEqual(code, 0)
        self.assertIn("dry-run", out)
        self.assertFalse(os.path.exists(self.dest))

    def test_uninstall_removes_skill_but_keeps_user_data(self):
        self.install()
        os.makedirs(os.path.join(self.target, "teixugo-relatorios"))
        with open(os.path.join(self.target, "teixugo-relatorios", "x.md"), "w", encoding="utf-8") as fh:
            fh.write("meu")
        code, out = self.install("--uninstall")
        self.assertEqual(code, 0, out)
        self.assertFalse(os.path.exists(os.path.join(self.target, "SKILL.md")))
        self.assertFalse(os.path.exists(os.path.join(self.target, "scripts")))
        self.assertTrue(os.path.exists(os.path.join(self.target, "teixugo-relatorios", "x.md")))
        self.assertIn("Mantidos", out)

    def test_uninstall_removes_empty_folder_and_is_idempotent(self):
        self.install()
        self.assertEqual(self.install("--uninstall")[0], 0)
        self.assertFalse(os.path.exists(self.target))
        code, out = self.install("--uninstall")
        self.assertEqual(code, 0)
        self.assertIn("Nada para desinstalar", out)

    def test_project_flag_installs_under_dot_claude(self):
        code, out = run_installer("--project", cwd=self.tmp.name)
        self.assertEqual(code, 0, out)
        self.assertTrue(os.path.exists(os.path.join(self.tmp.name, ".claude", "skills", SKILL, "SKILL.md")))

    def test_help_version_and_bad_usage(self):
        self.assertEqual(run_installer("--help")[0], 0)
        with open(os.path.join(ROOT, "package.json"), encoding="utf-8") as fh:
            version = json.load(fh)["version"]
        code, out = run_installer("--version")
        self.assertEqual((code, out.strip()), (0, version))
        code, out = run_installer("--wat")
        self.assertEqual(code, 2)
        self.assertIn("--wat", out)
        self.assertEqual(run_installer("--dest")[0], 2)

    def test_english_messages(self):
        r = subprocess.run([NODE, INSTALL, "--lang", "en", "--dest", self.dest, "--dry-run"], capture_output=True, text=True, encoding="utf-8")
        self.assertIn("would copy", r.stdout)


AGENT_NAMES = ["teixugo-redteam.md", "teixugo-scout.md", "teixugo-verifier.md"]


def run_with_home(home, *args, cwd=None):
    env = dict(os.environ, HOME=home, USERPROFILE=home)
    r = subprocess.run([NODE, INSTALL, "--lang", "pt", *args], cwd=cwd, env=env, capture_output=True, text=True, encoding="utf-8", timeout=60)
    return r.returncode, r.stdout + r.stderr


@unittest.skipUnless(NODE, "Node.js não encontrado")
class InstallerAgents(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.home = os.path.join(self.tmp.name, "home")
        os.makedirs(self.home)
        self.skill = os.path.join(self.home, ".claude", "skills", SKILL)
        self.agents = os.path.join(self.home, ".claude", "agents")

    def installed_agents(self):
        return sorted(os.listdir(self.agents)) if os.path.isdir(self.agents) else []

    def test_default_install_puts_skill_and_agents_in_the_claude_folders(self):
        code, out = run_with_home(self.home)
        self.assertEqual(code, 0, out)
        self.assertTrue(os.path.exists(os.path.join(self.skill, "SKILL.md")))
        self.assertEqual(self.installed_agents(), AGENT_NAMES)
        self.assertIn("Agentes: 3 instalado(s)", out)
        with open(os.path.join(self.skill, ".installed-agents"), encoding="utf-8") as fh:
            self.assertEqual(fh.read().split(), AGENT_NAMES)

    def test_installed_agent_files_are_identical_to_the_source(self):
        run_with_home(self.home)
        for name in AGENT_NAMES:
            with open(os.path.join(ROOT, "agents", name), "rb") as a, open(os.path.join(self.agents, name), "rb") as b:
                self.assertEqual(a.read(), b.read(), name)

    def test_project_install_uses_project_claude_folder(self):
        project = os.path.join(self.tmp.name, "proj")
        os.makedirs(project)
        code, out = run_with_home(self.home, "--project", cwd=project)
        self.assertEqual(code, 0, out)
        self.assertEqual(sorted(os.listdir(os.path.join(project, ".claude", "agents"))), AGENT_NAMES)
        self.assertFalse(os.path.exists(self.agents), "o --project não deve tocar na pasta pessoal")

    def test_no_agents_flag(self):
        code, _ = run_with_home(self.home, "--no-agents")
        self.assertEqual(code, 0)
        self.assertTrue(os.path.exists(os.path.join(self.skill, "SKILL.md")))
        self.assertFalse(os.path.exists(self.agents))

    def test_dest_alone_skips_agents_but_agents_dest_adds_them(self):
        dest, adest = os.path.join(self.tmp.name, "outro-agente"), os.path.join(self.tmp.name, "meus-agentes")
        run_with_home(self.home, "--dest", dest)
        self.assertFalse(os.path.exists(self.agents))
        code, _ = run_with_home(self.home, "--dest", dest, "--agents-dest", adest)
        self.assertEqual(code, 0)
        self.assertEqual(sorted(os.listdir(adest)), AGENT_NAMES)

    def test_users_own_agent_with_the_same_name_is_not_overwritten(self):
        os.makedirs(self.agents)
        mine = os.path.join(self.agents, "teixugo-scout.md")
        with open(mine, "w", encoding="utf-8") as fh:
            fh.write("---\nname: teixugo-scout\ndescription: meu\n---\nmeu agente\n")
        code, out = run_with_home(self.home)
        self.assertEqual(code, 0, out)
        self.assertIn("mantido", out)
        with open(mine, encoding="utf-8") as fh:
            self.assertIn("meu agente", fh.read())
        # e a desinstalação também não apaga o que não era do instalador
        run_with_home(self.home, "--uninstall")
        self.assertTrue(os.path.exists(mine))
        self.assertEqual(self.installed_agents(), ["teixugo-scout.md"])

    def test_force_overwrites_users_agent(self):
        os.makedirs(self.agents)
        mine = os.path.join(self.agents, "teixugo-scout.md")
        with open(mine, "w", encoding="utf-8") as fh:
            fh.write("meu agente")
        run_with_home(self.home, "--force")
        with open(mine, encoding="utf-8") as fh:
            self.assertIn("batedor", fh.read())

    def test_update_removes_agents_the_new_version_no_longer_ships_and_keeps_users(self):
        run_with_home(self.home)
        ghost = os.path.join(self.agents, "teixugo-fantasma.md")
        with open(ghost, "w", encoding="utf-8") as fh:
            fh.write("agente de uma versão antiga")
        with open(os.path.join(self.skill, ".installed-agents"), "a", encoding="utf-8") as fh:
            fh.write("teixugo-fantasma.md\n")  # o instalador o havia colocado
        other = os.path.join(self.agents, "revisor-do-usuario.md")
        with open(other, "w", encoding="utf-8") as fh:
            fh.write("do usuário")
        code, _ = run_with_home(self.home)
        self.assertEqual(code, 0)
        self.assertFalse(os.path.exists(ghost))
        self.assertTrue(os.path.exists(other))
        self.assertEqual([n for n in self.installed_agents() if n.startswith("teixugo-")], AGENT_NAMES)

    def test_uninstall_removes_skill_and_its_agents_only(self):
        run_with_home(self.home)
        other = os.path.join(self.agents, "revisor-do-usuario.md")
        with open(other, "w", encoding="utf-8") as fh:
            fh.write("do usuário")
        code, out = run_with_home(self.home, "--uninstall")
        self.assertEqual(code, 0, out)
        self.assertIn("Agentes removidos", out)
        self.assertFalse(os.path.exists(self.skill))
        self.assertEqual(self.installed_agents(), ["revisor-do-usuario.md"])

    def test_dry_run_touches_nothing(self):
        code, out = run_with_home(self.home, "--dry-run")
        self.assertEqual(code, 0)
        self.assertIn("agente(s)", out)
        self.assertFalse(os.path.exists(os.path.join(self.home, ".claude")))

    def test_installed_agents_pass_the_privilege_check(self):
        run_with_home(self.home)
        for name in ("teixugo-scout.md", "teixugo-verifier.md"):
            with open(os.path.join(self.agents, name), encoding="utf-8") as fh:
                m = re.search(r"^tools:\s*(.+)$", fh.read(), re.M)
            self.assertEqual({t.strip() for t in m.group(1).split(",")}, {"WebSearch", "WebFetch"})


class PackageMetadata(unittest.TestCase):
    """O pacote npm, a skill e o changelog precisam concordar."""

    def setUp(self):
        with open(os.path.join(ROOT, "package.json"), encoding="utf-8") as fh:
            self.pkg = json.load(fh)

    def test_versions_agree(self):
        sys.path.insert(0, os.path.join(ROOT, "scripts"))
        from tx import __version__

        self.assertEqual(self.pkg["version"], __version__)
        with open(os.path.join(ROOT, "CHANGELOG.md"), encoding="utf-8") as fh:
            self.assertRegex(fh.read(), rf"## \[{re.escape(self.pkg['version'])}\]")

    def test_bin_and_files_exist(self):
        self.assertEqual(self.pkg["name"], SKILL)
        self.assertTrue(os.path.exists(os.path.join(ROOT, self.pkg["bin"][SKILL])))
        for entry in self.pkg["files"]:
            self.assertTrue(os.path.exists(os.path.join(ROOT, entry.rstrip("/"))), entry)

    def test_package_ships_everything_the_installer_copies_and_no_tests(self):
        self.assertNotIn("tests/", self.pkg["files"])
        for needed in ("SKILL.md", "scripts/", "references/", "bin/", "LICENSE"):
            self.assertIn(needed, self.pkg["files"])


if __name__ == "__main__":
    unittest.main()
