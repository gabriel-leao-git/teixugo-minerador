#!/usr/bin/env node
'use strict';

/*
 * Instalador da skill teixugo-minerador.
 *
 *   npx github:gabriel-leao-git/teixugo-minerador          instala para todos os seus projetos
 *   npx github:gabriel-leao-git/teixugo-minerador --project instala só no projeto atual
 *
 * Sem dependências. Copia a skill para <skills>/teixugo-minerador. Só toca nos arquivos da própria
 * skill (lista MANAGED): relatórios, vigilâncias e qualquer outra coisa que você tenha na pasta
 * de destino são preservados na atualização e na desinstalação.
 */

const fs = require('fs');
const os = require('os');
const path = require('path');
const { spawnSync } = require('child_process');

const pkg = require('../package.json');

const SKILL = 'teixugo-minerador';
const ROOT = path.resolve(__dirname, '..');
const MANAGED = [
  'SKILL.md',
  'references',
  'scripts',
  'examples',
  'README.md',
  'README.pt-BR.md',
  'CHANGELOG.md',
  'LICENSE',
  'requirements-optional.txt',
];
const VERSION_FILE = '.installed-version';
const SKIP_NAMES = new Set(['__pycache__', '.DS_Store', 'Thumbs.db']);

const MSG = {
  pt: {
    help: `Instala a skill ${SKILL} para o Claude Code.

Uso:
  npx github:gabriel-leao-git/${SKILL} [opções]

Opções:
  (nenhuma)        instala em ~/.claude/skills (todos os seus projetos)
  --project        instala em ./.claude/skills (só o projeto atual)
  --dest <pasta>   instala em <pasta>/${SKILL} (pasta de skills de outro agente, por exemplo)
  --dry-run        mostra o que seria feito, sem alterar nada
  --force          sobrescreve/remove mesmo que a pasta de destino não seja desta skill
  --uninstall      remove a skill (arquivos seus, como relatórios, são mantidos)
  --lang pt|en     idioma das mensagens
  -v, --version    mostra a versão
  -h, --help       mostra esta ajuda`,
    unknownOpt: (o) => `Opção desconhecida: ${o}. Use --help.`,
    needValue: (o) => `A opção ${o} precisa de um valor.`,
    foreign: (t) => `A pasta ${t} já existe e não parece ser desta skill. Nada foi alterado. Use --force para sobrescrever.`,
    installing: (t) => `Instalando em ${t}`,
    updating: (t, a, b) => `Atualizando ${t} (${a} -> ${b})`,
    wouldCopy: (n) => `[dry-run] copiaria ${n} arquivo(s)`,
    wouldRemove: (n) => `[dry-run] removeria ${n} item(ns) antigo(s) da skill`,
    done: (n, t) => `Pronto: ${n} arquivo(s) em ${t}`,
    notInstalled: (t) => `Nada para desinstalar em ${t}.`,
    removed: (t) => `Skill removida de ${t}`,
    kept: (t, names) => `Mantidos (são seus): ${names.join(', ')} em ${t}`,
    next: 'Próximos passos',
    useIt: 'Abra o Claude Code e peça, por exemplo: "vá à caça de 3 produtos para a dor remover pelo de cachorro" (ou digite /teixugo-minerador).',
    pyOk: (v) => `Python encontrado: ${v}`,
    pyMissing: 'Python 3.9+ não encontrado: os scripts (validação, relatórios, sonar) precisam dele. Sem Python, a skill ainda funciona, mas escreve o relatório à mão.',
    optional: 'Para gerar Word, Excel e PDF: pip install -r requirements-optional.txt (na pasta da skill).',
    runFrom: 'Rode os scripts a partir da sua pasta de trabalho: os relatórios saem em ./teixugo-relatorios.',
  },
  en: {
    help: `Installs the ${SKILL} skill for Claude Code.

Usage:
  npx github:gabriel-leao-git/${SKILL} [options]

Options:
  (none)           install into ~/.claude/skills (all your projects)
  --project        install into ./.claude/skills (current project only)
  --dest <dir>     install into <dir>/${SKILL} (another agent's skills folder, for example)
  --dry-run        show what would happen without changing anything
  --force          overwrite/remove even if the target folder is not this skill
  --uninstall      remove the skill (your own files, such as reports, are kept)
  --lang pt|en     message language
  -v, --version    print the version
  -h, --help       print this help`,
    unknownOpt: (o) => `Unknown option: ${o}. Use --help.`,
    needValue: (o) => `Option ${o} needs a value.`,
    foreign: (t) => `Folder ${t} already exists and does not look like this skill. Nothing was changed. Use --force to overwrite.`,
    installing: (t) => `Installing into ${t}`,
    updating: (t, a, b) => `Updating ${t} (${a} -> ${b})`,
    wouldCopy: (n) => `[dry-run] would copy ${n} file(s)`,
    wouldRemove: (n) => `[dry-run] would remove ${n} old skill item(s)`,
    done: (n, t) => `Done: ${n} file(s) in ${t}`,
    notInstalled: (t) => `Nothing to uninstall at ${t}.`,
    removed: (t) => `Skill removed from ${t}`,
    kept: (t, names) => `Kept (they are yours): ${names.join(', ')} in ${t}`,
    next: 'Next steps',
    useIt: 'Open Claude Code and ask, for example: "go hunt 3 products for the pain of removing dog hair" (or type /teixugo-minerador).',
    pyOk: (v) => `Python found: ${v}`,
    pyMissing: 'Python 3.9+ not found: the scripts (validation, reports, sonar) need it. Without Python the skill still works, but writes the report by hand.',
    optional: 'For Word, Excel and PDF output: pip install -r requirements-optional.txt (in the skill folder).',
    runFrom: 'Run the scripts from your working folder: reports go to ./teixugo-relatorios.',
  },
};

function detectLang(argv) {
  const i = argv.indexOf('--lang');
  if (i !== -1 && argv[i + 1]) return argv[i + 1].toLowerCase().startsWith('pt') ? 'pt' : 'en';
  const env = (process.env.LC_ALL || process.env.LANG || '').toLowerCase();
  let locale = env;
  if (!locale) {
    try {
      locale = Intl.DateTimeFormat().resolvedOptions().locale.toLowerCase();
    } catch (_) {
      locale = '';
    }
  }
  return locale.startsWith('pt') ? 'pt' : 'en';
}

function parseArgs(argv) {
  const o = { project: false, dest: null, dryRun: false, force: false, uninstall: false, help: false, version: false, bad: null, needs: null };
  for (let i = 0; i < argv.length; i++) {
    const a = argv[i];
    if (a === '--project') o.project = true;
    else if (a === '--dry-run') o.dryRun = true;
    else if (a === '--force') o.force = true;
    else if (a === '--uninstall') o.uninstall = true;
    else if (a === '-h' || a === '--help') o.help = true;
    else if (a === '-v' || a === '--version') o.version = true;
    else if (a === '--dest' || a === '--lang') {
      const v = argv[i + 1];
      if (v === undefined || v.startsWith('--')) {
        o.needs = a;
        break;
      }
      if (a === '--dest') o.dest = v;
      i++;
    } else {
      o.bad = a;
      break;
    }
  }
  return o;
}

function targetDir(o) {
  if (o.dest) return path.join(path.resolve(o.dest), SKILL);
  if (o.project) return path.join(process.cwd(), '.claude', 'skills', SKILL);
  return path.join(os.homedir(), '.claude', 'skills', SKILL);
}

function listFiles(src, rel = '') {
  const out = [];
  for (const name of fs.readdirSync(path.join(src, rel))) {
    if (SKIP_NAMES.has(name) || name.endsWith('.pyc')) continue;
    const r = path.join(rel, name);
    const full = path.join(src, r);
    if (fs.statSync(full).isDirectory()) out.push(...listFiles(src, r));
    else out.push(r);
  }
  return out;
}

function sourceFiles() {
  const files = [];
  for (const item of MANAGED) {
    const full = path.join(ROOT, item);
    if (!fs.existsSync(full)) continue;
    if (fs.statSync(full).isDirectory()) files.push(...listFiles(ROOT, item));
    else files.push(item);
  }
  return files;
}

function isOurSkill(dir) {
  try {
    const head = fs.readFileSync(path.join(dir, 'SKILL.md'), 'utf8').slice(0, 2000);
    return new RegExp(`^name:\\s*${SKILL}\\s*$`, 'm').test(head);
  } catch (_) {
    return false;
  }
}

function installedVersion(dir) {
  try {
    return fs.readFileSync(path.join(dir, VERSION_FILE), 'utf8').trim() || '?';
  } catch (_) {
    return '?';
  }
}

function removeManaged(dir) {
  let n = 0;
  for (const item of MANAGED.concat([VERSION_FILE])) {
    const p = path.join(dir, item);
    if (fs.existsSync(p)) {
      fs.rmSync(p, { recursive: true, force: true });
      n++;
    }
  }
  return n;
}

function managedPresent(dir) {
  return MANAGED.filter((item) => fs.existsSync(path.join(dir, item))).length;
}

function pythonVersion() {
  for (const cmd of ['python3', 'python', 'py']) {
    const r = spawnSync(cmd, ['--version'], { encoding: 'utf8', timeout: 5000 });
    if (r.status === 0) {
      const text = `${r.stdout || ''}${r.stderr || ''}`.trim();
      const m = text.match(/Python (\d+)\.(\d+)/);
      if (m && (Number(m[1]) > 3 || (Number(m[1]) === 3 && Number(m[2]) >= 9))) return text;
    }
  }
  return null;
}

function main(argv) {
  const lang = detectLang(argv);
  const t = MSG[lang];
  const o = parseArgs(argv);
  if (o.needs) {
    console.error(t.needValue(o.needs));
    return 2;
  }
  if (o.bad) {
    console.error(t.unknownOpt(o.bad));
    return 2;
  }
  if (o.help) {
    console.log(t.help);
    return 0;
  }
  if (o.version) {
    console.log(pkg.version);
    return 0;
  }

  const target = targetDir(o);
  const exists = fs.existsSync(target);

  if (o.uninstall) {
    if (!exists) {
      console.log(t.notInstalled(target));
      return 0;
    }
    if (!isOurSkill(target) && !o.force) {
      console.error(t.foreign(target));
      return 1;
    }
    if (o.dryRun) {
      console.log(t.wouldRemove(managedPresent(target)));
      return 0;
    }
    removeManaged(target);
    const rest = fs.readdirSync(target);
    if (rest.length === 0) fs.rmdirSync(target);
    console.log(t.removed(target));
    if (rest.length) console.log(t.kept(target, rest));
    return 0;
  }

  if (exists && !isOurSkill(target) && !o.force) {
    console.error(t.foreign(target));
    return 1;
  }

  const files = sourceFiles();
  if (!files.includes('SKILL.md')) {
    console.error('SKILL.md não encontrado no pacote / SKILL.md not found in the package.');
    return 1;
  }
  const updating = exists && isOurSkill(target);
  console.log(updating ? t.updating(target, installedVersion(target), pkg.version) : t.installing(target));

  if (o.dryRun) {
    if (updating) console.log(t.wouldRemove(managedPresent(target)));
    console.log(t.wouldCopy(files.length));
    return 0;
  }

  if (exists) removeManaged(target); // atualização: some o que a versão nova não tem mais
  for (const rel of files) {
    const dst = path.join(target, rel);
    fs.mkdirSync(path.dirname(dst), { recursive: true });
    fs.copyFileSync(path.join(ROOT, rel), dst);
  }
  fs.writeFileSync(path.join(target, VERSION_FILE), `${pkg.version}\n`);
  console.log(t.done(files.length, target));

  console.log(`\n${t.next}:`);
  console.log(`  - ${t.useIt}`);
  const py = pythonVersion();
  console.log(`  - ${py ? t.pyOk(py) : t.pyMissing}`);
  console.log(`  - ${t.optional}`);
  console.log(`  - ${t.runFrom}`);
  return 0;
}

process.exitCode = main(process.argv.slice(2));
