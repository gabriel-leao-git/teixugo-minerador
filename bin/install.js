#!/usr/bin/env node
'use strict';

/*
 * Instalador da skill teixugo-minerador (e dos agentes de apoio).
 *
 *   npx github:gabriel-leao-git/teixugo-minerador            instala para todos os seus projetos
 *   npx github:gabriel-leao-git/teixugo-minerador --project   instala só no projeto atual
 *
 * Sem dependências. Copia a skill para <skills>/teixugo-minerador e os agentes (agents/*.md) para a
 * pasta de agentes. Só toca nos arquivos da própria skill (lista MANAGED) e nos agentes que ele mesmo
 * instalou (lista em .installed-agents): relatórios, vigilâncias e qualquer outra coisa que você tenha
 * ali são preservados na atualização e na desinstalação, e um agente seu com o mesmo nome não é
 * sobrescrito sem --force.
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
const AGENTS_MANIFEST = '.installed-agents';
const AGENTS_SRC = path.join(ROOT, 'agents');
const SKIP_NAMES = new Set(['__pycache__', '.DS_Store', 'Thumbs.db']);

const MSG = {
  pt: {
    help: `Instala a skill ${SKILL} (e seus agentes de apoio) para o Claude Code.

Uso:
  npx github:gabriel-leao-git/${SKILL} [opções]

Opções:
  (nenhuma)          skill em ~/.claude/skills e agentes em ~/.claude/agents (todos os seus projetos)
  --project          skill em ./.claude/skills e agentes em ./.claude/agents (só o projeto atual)
  --dest <pasta>     skill em <pasta>/${SKILL} (pasta de skills de outro agente, por exemplo); sem agentes
  --agents-dest <p>  pasta dos agentes (junto com --dest, ou para trocar o padrão)
  --no-agents        não instala os agentes
  --dry-run          mostra o que seria feito, sem alterar nada
  --force            sobrescreve mesmo que a pasta/arquivo de destino não seja desta skill
  --uninstall        remove a skill e os agentes que este instalador colocou (arquivos seus são mantidos)
  --lang pt|en       idioma das mensagens
  -v, --version      mostra a versão
  -h, --help         mostra esta ajuda

Também dá para instalar como plugin do Claude Code:
  /plugin marketplace add gabriel-leao-git/${SKILL}
  /plugin install ${SKILL}@teixugo`,
    unknownOpt: (o) => `Opção desconhecida: ${o}. Use --help.`,
    needValue: (o) => `A opção ${o} precisa de um valor.`,
    foreign: (t) => `A pasta ${t} já existe e não parece ser desta skill. Nada foi alterado. Use --force para sobrescrever.`,
    installing: (t) => `Instalando em ${t}`,
    updating: (t, a, b) => `Atualizando ${t} (${a} -> ${b})`,
    wouldCopy: (n) => `[dry-run] copiaria ${n} arquivo(s)`,
    wouldRemove: (n) => `[dry-run] removeria ${n} item(ns) antigo(s) da skill`,
    wouldAgents: (n, d) => `[dry-run] instalaria ${n} agente(s) em ${d}`,
    wouldRemoveAgents: (n, d) => `[dry-run] removeria ${n} agente(s) de ${d}`,
    done: (n, t) => `Pronto: ${n} arquivo(s) em ${t}`,
    agentsDone: (n, d) => `Agentes: ${n} instalado(s) em ${d}`,
    agentSkipped: (f) => `Agente ${f} já existe e não foi instalado por este instalador: mantido (use --force para sobrescrever).`,
    agentsRemoved: (n, d) => `Agentes removidos de ${d}: ${n}`,
    notInstalled: (t) => `Nada para desinstalar em ${t}.`,
    removed: (t) => `Skill removida de ${t}`,
    kept: (t, names) => `Mantidos (são seus): ${names.join(', ')} em ${t}`,
    next: 'Próximos passos',
    useIt: 'Abra o Claude Code e peça, por exemplo: "vá à caça de 3 produtos para a dor remover pelo de cachorro" (ou digite /teixugo-minerador).',
    pyOk: (v) => `Python encontrado: ${v}`,
    pyMissing: 'Python 3.9+ não encontrado: os scripts (validação, relatórios, sonar) precisam dele. Sem Python, a skill ainda funciona, mas escreve o relatório à mão.',
    optional: 'Para gerar Word, Excel e PDF: pip install -r requirements-optional.txt (na pasta da skill).',
    runFrom: 'Rode os scripts a partir da sua pasta de trabalho: os relatórios saem em ./teixugo-relatorios.',
    agentsHint: 'Agentes disponíveis: teixugo-scout (descoberta), teixugo-verifier (verificação) e teixugo-redteam (revisão). A skill os usa em pesquisas grandes.',
  },
  en: {
    help: `Installs the ${SKILL} skill (and its helper agents) for Claude Code.

Usage:
  npx github:gabriel-leao-git/${SKILL} [options]

Options:
  (none)             skill in ~/.claude/skills and agents in ~/.claude/agents (all your projects)
  --project          skill in ./.claude/skills and agents in ./.claude/agents (current project only)
  --dest <dir>       skill in <dir>/${SKILL} (another agent's skills folder, for example); no agents
  --agents-dest <d>  agents folder (together with --dest, or to change the default)
  --no-agents        do not install the agents
  --dry-run          show what would happen without changing anything
  --force            overwrite even if the target folder/file is not this skill's
  --uninstall        remove the skill and the agents this installer put there (your own files are kept)
  --lang pt|en       message language
  -v, --version      print the version
  -h, --help         print this help

You can also install it as a Claude Code plugin:
  /plugin marketplace add gabriel-leao-git/${SKILL}
  /plugin install ${SKILL}@teixugo`,
    unknownOpt: (o) => `Unknown option: ${o}. Use --help.`,
    needValue: (o) => `Option ${o} needs a value.`,
    foreign: (t) => `Folder ${t} already exists and does not look like this skill. Nothing was changed. Use --force to overwrite.`,
    installing: (t) => `Installing into ${t}`,
    updating: (t, a, b) => `Updating ${t} (${a} -> ${b})`,
    wouldCopy: (n) => `[dry-run] would copy ${n} file(s)`,
    wouldRemove: (n) => `[dry-run] would remove ${n} old skill item(s)`,
    wouldAgents: (n, d) => `[dry-run] would install ${n} agent(s) in ${d}`,
    wouldRemoveAgents: (n, d) => `[dry-run] would remove ${n} agent(s) from ${d}`,
    done: (n, t) => `Done: ${n} file(s) in ${t}`,
    agentsDone: (n, d) => `Agents: ${n} installed in ${d}`,
    agentSkipped: (f) => `Agent ${f} already exists and was not installed by this installer: kept (use --force to overwrite).`,
    agentsRemoved: (n, d) => `Agents removed from ${d}: ${n}`,
    notInstalled: (t) => `Nothing to uninstall at ${t}.`,
    removed: (t) => `Skill removed from ${t}`,
    kept: (t, names) => `Kept (they are yours): ${names.join(', ')} in ${t}`,
    next: 'Next steps',
    useIt: 'Open Claude Code and ask, for example: "go hunt 3 products for the pain of removing dog hair" (or type /teixugo-minerador).',
    pyOk: (v) => `Python found: ${v}`,
    pyMissing: 'Python 3.9+ not found: the scripts (validation, reports, sonar) need it. Without Python the skill still works, but writes the report by hand.',
    optional: 'For Word, Excel and PDF output: pip install -r requirements-optional.txt (in the skill folder).',
    runFrom: 'Run the scripts from your working folder: reports go to ./teixugo-relatorios.',
    agentsHint: 'Available agents: teixugo-scout (discovery), teixugo-verifier (verification) and teixugo-redteam (review). The skill uses them on larger research jobs.',
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
  const o = {
    project: false, dest: null, agentsDest: null, noAgents: false, dryRun: false, force: false,
    uninstall: false, help: false, version: false, bad: null, needs: null,
  };
  for (let i = 0; i < argv.length; i++) {
    const a = argv[i];
    if (a === '--project') o.project = true;
    else if (a === '--no-agents') o.noAgents = true;
    else if (a === '--dry-run') o.dryRun = true;
    else if (a === '--force') o.force = true;
    else if (a === '--uninstall') o.uninstall = true;
    else if (a === '-h' || a === '--help') o.help = true;
    else if (a === '-v' || a === '--version') o.version = true;
    else if (a === '--dest' || a === '--agents-dest' || a === '--lang') {
      const v = argv[i + 1];
      if (v === undefined || v.startsWith('--')) {
        o.needs = a;
        break;
      }
      if (a === '--dest') o.dest = v;
      if (a === '--agents-dest') o.agentsDest = v;
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

function agentsTarget(o) {
  if (o.noAgents) return null;
  if (o.agentsDest) return path.resolve(o.agentsDest);
  if (o.dest) return null; // pasta de skills de outro agente: não mexe nos agentes do Claude Code
  if (o.project) return path.join(process.cwd(), '.claude', 'agents');
  return path.join(os.homedir(), '.claude', 'agents');
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

function agentSources() {
  if (!fs.existsSync(AGENTS_SRC)) return [];
  return fs.readdirSync(AGENTS_SRC).filter((f) => f.endsWith('.md')).sort();
}

function isOurSkill(dir) {
  try {
    const head = fs.readFileSync(path.join(dir, 'SKILL.md'), 'utf8').slice(0, 2000);
    return new RegExp(`^name:\\s*${SKILL}\\s*$`, 'm').test(head);
  } catch (_) {
    return false;
  }
}

function readLines(file) {
  try {
    return fs.readFileSync(file, 'utf8').split(/\r?\n/).map((s) => s.trim()).filter(Boolean);
  } catch (_) {
    return [];
  }
}

function installedVersion(dir) {
  const v = readLines(path.join(dir, VERSION_FILE))[0];
  return v || '?';
}

function removeManaged(dir) {
  let n = 0;
  for (const item of MANAGED.concat([VERSION_FILE, AGENTS_MANIFEST])) {
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

/* Instala os agentes; devolve {installed, skipped}. `previous` = nomes que este instalador já havia colocado. */
function installAgents(dir, previous, force, t) {
  const sources = agentSources();
  fs.mkdirSync(dir, { recursive: true });
  for (const old of previous) {
    if (!sources.includes(old)) fs.rmSync(path.join(dir, old), { force: true }); // agente que a versão nova não tem mais
  }
  const installed = [];
  for (const f of sources) {
    const dst = path.join(dir, f);
    const content = fs.readFileSync(path.join(AGENTS_SRC, f));
    if (fs.existsSync(dst) && !previous.includes(f) && !force && !fs.readFileSync(dst).equals(content)) {
      console.log(`  ! ${t.agentSkipped(f)}`);
      continue; // arquivo do usuário com o mesmo nome
    }
    fs.writeFileSync(dst, content);
    installed.push(f);
  }
  return installed;
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
  const agentsDir = agentsTarget(o);
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
    const tracked = readLines(path.join(target, AGENTS_MANIFEST));
    if (o.dryRun) {
      console.log(t.wouldRemove(managedPresent(target)));
      if (agentsDir && tracked.length) console.log(t.wouldRemoveAgents(tracked.length, agentsDir));
      return 0;
    }
    let removedAgents = 0;
    if (agentsDir) {
      for (const f of tracked) {
        const p = path.join(agentsDir, f);
        if (fs.existsSync(p)) {
          fs.rmSync(p, { force: true });
          removedAgents++;
        }
      }
    }
    removeManaged(target);
    const rest = fs.readdirSync(target);
    if (rest.length === 0) fs.rmdirSync(target);
    console.log(t.removed(target));
    if (removedAgents) console.log(t.agentsRemoved(removedAgents, agentsDir));
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
    if (agentsDir) console.log(t.wouldAgents(agentSources().length, agentsDir));
    return 0;
  }

  const previousAgents = exists ? readLines(path.join(target, AGENTS_MANIFEST)) : [];
  if (exists) removeManaged(target); // atualização: some o que a versão nova não tem mais
  for (const rel of files) {
    const dst = path.join(target, rel);
    fs.mkdirSync(path.dirname(dst), { recursive: true });
    fs.copyFileSync(path.join(ROOT, rel), dst);
  }
  fs.writeFileSync(path.join(target, VERSION_FILE), `${pkg.version}\n`);
  console.log(t.done(files.length, target));

  let installedAgents = [];
  if (agentsDir) {
    installedAgents = installAgents(agentsDir, previousAgents, o.force, t);
    fs.writeFileSync(path.join(target, AGENTS_MANIFEST), installedAgents.join('\n') + (installedAgents.length ? '\n' : ''));
    console.log(t.agentsDone(installedAgents.length, agentsDir));
  }

  console.log(`\n${t.next}:`);
  console.log(`  - ${t.useIt}`);
  if (installedAgents.length) console.log(`  - ${t.agentsHint}`);
  const py = pythonVersion();
  console.log(`  - ${py ? t.pyOk(py) : t.pyMissing}`);
  console.log(`  - ${t.optional}`);
  console.log(`  - ${t.runFrom}`);
  return 0;
}

process.exitCode = main(process.argv.slice(2));
