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
