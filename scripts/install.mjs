#!/usr/bin/env node

import {
  intro, outro, cancel, confirm, text, select,
  group, isCancel,
  spinner, note, log,
} from '@clack/prompts';
import { paginatedGroupMultiselect, styledMultiselect } from './lib/paginated-group-multiselect.mjs';
import { execSync } from 'node:child_process';
import fs from 'node:fs';
import os from 'node:os';
import path from 'node:path';

const HOME = os.homedir();
const expand = (s) => (s === '~' ? HOME : s.startsWith('~/') ? path.join(HOME, s.slice(2)) : s);
const shorten = (s) => s.replace(HOME, '~');
const SCRIPT_DIR = path.dirname(new URL(import.meta.url).pathname);
const PACKAGE_ROOT = path.resolve(SCRIPT_DIR, '..');

import {
  UNIVERSAL_PATH, UNIVERSAL_AGENTS, SKILL_GROUPS, COMMAND_LIST, AGENT_LIST,
} from './lib/catalog.mjs';

const REPO_URL = 'https://github.com/notdp/.dotfiles.git';
const IGNORE_DIRS = new Set(['.system', '.git', '.github', '.ruff_cache', 'node_modules']);

function toProjectPath(p) {
  if (p === '~') return '.';
  if (p.startsWith('~/')) return p.slice(2);
  return p;
}

function projectCatalog(items) {
  return items.map(o => {
    const projPath = toProjectPath(o.value);
    const name = o.label.replace(/\s*\(.*\)$/, '');
    return { ...o, value: projPath, label: `${name} (${projPath})` };
  });
}

function projectGroups(groups) {
  const out = {};
  for (const [key, items] of Object.entries(groups)) {
    out[key] = projectCatalog(items);
  }
  return out;
}

// ── Helpers ──────────────────────────────────────────────────

function isLinkedTo(linkPath, target) {
  try { return fs.readlinkSync(expand(linkPath)) === target; }
  catch { return false; }
}

function createLink(linkPath, target) {
  const full = expand(linkPath);
  if (isLinkedTo(linkPath, target)) return 'exists';

  try {
    const stat = fs.lstatSync(full);
    if (stat.isSymbolicLink()) {
      fs.unlinkSync(full);
    } else if (stat.isDirectory()) {
      const bak = `${full}.bak-${Date.now()}`;
      fs.renameSync(full, bak);
      try { execSync(`rsync -a --ignore-existing "${bak}/" "${target}/"`, { stdio: 'pipe' }); }
      catch { try { execSync(`cp -an "${bak}/." "${target}/"`, { stdio: 'pipe' }); } catch {} }
    } else if (stat.isFile()) {
      fs.renameSync(full, `${full}.bak-${Date.now()}`);
    }
  } catch (err) {
    if (err.code !== 'ENOENT') throw err;
  }

  fs.mkdirSync(path.dirname(full), { recursive: true });
  fs.symlinkSync(target, full);
  return 'created';
}

function createCopy(destPath, source) {
  const full = expand(destPath);
  fs.mkdirSync(path.dirname(full), { recursive: true });

  const srcStat = fs.statSync(source);
  if (srcStat.isDirectory()) {
    fs.mkdirSync(full, { recursive: true });
    try { execSync(`rsync -a "${source}/" "${full}/"`, { stdio: 'pipe' }); }
    catch { execSync(`cp -r "${source}/." "${full}/"`, { stdio: 'pipe' }); }
  } else {
    fs.copyFileSync(source, full);
  }
  return 'created';
}

function ensureFrontMatter(dir) {
  if (!fs.existsSync(dir)) return;
  for (const file of fs.readdirSync(dir).filter(f => f.endsWith('.md'))) {
    const fp = path.join(dir, file);
    const content = fs.readFileSync(fp, 'utf-8');
    if (content.startsWith('---')) continue;
    fs.writeFileSync(fp, `---\ndescription:\n---\n\n${content}`);
  }
}

function linkedValues(catalog, target) {
  const items = Array.isArray(catalog)
    ? catalog
    : Object.values(catalog).flat();
  return items.filter(o => isLinkedTo(o.value, target)).map(o => o.value);
}

function annotate(items, target) {
  return items.map(o => ({
    ...o,
    hint: isLinkedTo(o.value, target) ? 'linked' : o.hint,
  }));
}

function annotateGroups(groups, target) {
  const out = {};
  for (const [key, items] of Object.entries(groups)) {
    out[key] = annotate(items, target);
  }
  return out;
}

// ── Catalog ──────────────────────────────────────────────────



// ── Initialization helpers ───────────────────────────────────

function scanDir(dir) {
  if (!fs.existsSync(dir)) return [];
  return fs.readdirSync(dir, { withFileTypes: true })
    .filter(d => d.isDirectory() && !d.name.startsWith('.') && !IGNORE_DIRS.has(d.name))
    .map(d => d.name);
}

function needsInit(dotfilesDir) {
  const skillsDir = path.join(dotfilesDir, 'skills');
  const commandsDir = path.join(dotfilesDir, 'commands');
  if (!fs.existsSync(dotfilesDir)) return true;
  const hasSkills = fs.existsSync(skillsDir) && scanDir(skillsDir).length > 0;
  const hasCommands = fs.existsSync(commandsDir) && fs.readdirSync(commandsDir).some(f => f.endsWith('.md') && f !== '.gitkeep');
  return !hasSkills && !hasCommands;
}

function scanCommands(dir) {
  if (!fs.existsSync(dir)) return [];
  return fs.readdirSync(dir)
    .filter(f => f.endsWith('.md') && f !== '.gitkeep')
    .map(f => f.replace(/\.md$/, ''));
}

function hasPackageContent() {
  const s = path.join(PACKAGE_ROOT, 'skills');
  const c = path.join(PACKAGE_ROOT, 'commands');
  return (fs.existsSync(s) && scanDir(s).length > 0) ||
    (fs.existsSync(c) && scanCommands(c).length > 0);
}

// ── Main ─────────────────────────────────────────────────────

async function main() {
  intro('.dotfiles installer');

  // ── Step 1: Installation scope ──
  const scope = await select({
    message: 'Installation scope',
    options: [
      { value: 'global', label: 'Global', hint: 'Install in home directory (available across all projects)' },
      { value: 'project', label: 'Project', hint: 'Install in current directory (committed with your project)' },
    ],
  });
  if (isCancel(scope)) { cancel('Cancelled.'); process.exit(0); }

  const isGlobal = scope === 'global';

  // ── Step 2: Installation method ──
  const method = await select({
    message: 'Installation method',
    options: [
      { value: 'symlink', label: 'Symlink (Recommended)', hint: 'Single source of truth, easy updates' },
      { value: 'copy', label: 'Copy to all agents', hint: 'Independent copies for each agent' },
    ],
  });
  if (isCancel(method)) { cancel('Cancelled.'); process.exit(0); }

  // ── Step 3: Dotfiles directory ──
  const dirInput = await text({
    message: 'Dotfiles directory?',
    placeholder: isGlobal ? '~/.dotfiles' : '.agents',
    defaultValue: isGlobal ? '~/.dotfiles' : '.agents',
  });
  if (isCancel(dirInput)) { cancel('Cancelled.'); process.exit(0); }

  const DOTFILES_DIR = isGlobal
    ? expand(dirInput.trim())
    : path.resolve(dirInput.trim());

  const COMMANDS_DIR = path.join(DOTFILES_DIR, 'commands');
  const SKILLS_DIR = path.join(DOTFILES_DIR, 'skills');
  const AGENTS_FILE = path.join(DOTFILES_DIR, 'agents', 'AGENTS.md');

  // ── Step 4: Initialize if needed ──
  const isSameDir = path.resolve(PACKAGE_ROOT) === path.resolve(DOTFILES_DIR);

  if (!isSameDir && needsInit(DOTFILES_DIR)) {
    const usePackage = hasPackageContent();
    const sourceLabel = usePackage ? 'package' : 'GitHub';

    const wantPresets = await confirm({
      message: `Install pre-made skills & commands from ${sourceLabel}?`,
    });
    if (isCancel(wantPresets)) { cancel('Cancelled.'); process.exit(0); }

    if (wantPresets) {
      const s = spinner();

      if (usePackage) {
        s.start('Copying content from package...');
        fs.mkdirSync(DOTFILES_DIR, { recursive: true });
        for (const dir of ['skills', 'commands', 'agents']) {
          const src = path.join(PACKAGE_ROOT, dir);
          const dst = path.join(DOTFILES_DIR, dir);
          if (fs.existsSync(src)) {
            fs.mkdirSync(dst, { recursive: true });
            try { execSync(`rsync -a --ignore-existing "${src}/" "${dst}/"`, { stdio: 'pipe' }); }
            catch { execSync(`cp -r "${src}/." "${dst}/"`, { stdio: 'pipe' }); }
          }
        }
        s.stop('Content copied.');
      } else {
        s.start('Cloning repository...');
        try {
          if (fs.existsSync(DOTFILES_DIR)) {
            const tmp = path.join(os.tmpdir(), `dotfiles-${Date.now()}`);
            execSync(`git clone --depth 1 "${REPO_URL}" "${tmp}"`, { stdio: 'pipe' });
            for (const dir of ['skills', 'commands', 'agents']) {
              const src = path.join(tmp, dir);
              const dst = path.join(DOTFILES_DIR, dir);
              if (fs.existsSync(src)) {
                fs.mkdirSync(dst, { recursive: true });
                execSync(`rsync -a --ignore-existing "${src}/" "${dst}/"`, { stdio: 'pipe' });
              }
            }
            fs.rmSync(tmp, { recursive: true, force: true });
          } else {
            execSync(`git clone --depth 1 "${REPO_URL}" "${DOTFILES_DIR}"`, { stdio: 'pipe' });
          }
          s.stop('Repository cloned.');
        } catch (err) {
          s.stop('Clone failed.');
          log.warn(`git clone failed: ${err.message}`);
          log.info('Continuing with empty directories...');
          fs.mkdirSync(SKILLS_DIR, { recursive: true });
          fs.mkdirSync(COMMANDS_DIR, { recursive: true });
          fs.mkdirSync(path.dirname(AGENTS_FILE), { recursive: true });
        }
      }

      const availableSkills = scanDir(SKILLS_DIR);
      if (availableSkills.length > 0) {
        const selectedSkills = await styledMultiselect({
          message: 'Select skills to install',
          options: availableSkills.map(s => ({ value: s, label: s })),
          initialValues: availableSkills,
          required: false,
        });
        if (isCancel(selectedSkills)) { cancel('Cancelled.'); process.exit(0); }
        const keepSkills = new Set(selectedSkills || []);
        for (const s of availableSkills) {
          if (!keepSkills.has(s)) fs.rmSync(path.join(SKILLS_DIR, s), { recursive: true, force: true });
        }
      }

      const availableCommands = scanCommands(COMMANDS_DIR);
      if (availableCommands.length > 0) {
        const selectedCommands = await styledMultiselect({
          message: 'Select commands to install',
          options: availableCommands.map(c => ({ value: c, label: c })),
          initialValues: availableCommands,
          required: false,
        });
        if (isCancel(selectedCommands)) { cancel('Cancelled.'); process.exit(0); }
        const keepCommands = new Set((selectedCommands || []).map(c => `${c}.md`));
        for (const f of fs.readdirSync(COMMANDS_DIR)) {
          if (f.endsWith('.md') && f !== '.gitkeep' && !keepCommands.has(f)) fs.unlinkSync(path.join(COMMANDS_DIR, f));
        }
      }
    } else {
      fs.mkdirSync(SKILLS_DIR, { recursive: true });
      fs.mkdirSync(COMMANDS_DIR, { recursive: true });
      fs.mkdirSync(path.dirname(AGENTS_FILE), { recursive: true });
      if (isGlobal) {
        execSync('git init', { cwd: DOTFILES_DIR, stdio: 'pipe' });
        log.info(`Initialized git repository in ${shorten(DOTFILES_DIR)}`);
      }
    }
  }

  // Ensure directories exist
  fs.mkdirSync(COMMANDS_DIR, { recursive: true });
  fs.mkdirSync(SKILLS_DIR, { recursive: true });
  fs.mkdirSync(path.dirname(AGENTS_FILE), { recursive: true });

  if (isGlobal && !fs.existsSync(AGENTS_FILE)) {
    log.info('First install — merging existing agent config files...');
    let content = '';
    for (const opt of AGENT_LIST) {
      const file = expand(opt.value);
      try {
        const stat = fs.lstatSync(file);
        if (stat.isFile() && !stat.isSymbolicLink()) {
          content += `\n# === from ${opt.value} ===\n`;
          content += fs.readFileSync(file, 'utf-8');
        }
      } catch {}
    }
    fs.writeFileSync(AGENTS_FILE, content);
  }

  // ── Step 5: Select agent paths ──
  const projUniversalAgents = isGlobal ? UNIVERSAL_AGENTS : {
    [`Universal (${toProjectPath(UNIVERSAL_PATH)})`]: UNIVERSAL_AGENTS[Object.keys(UNIVERSAL_AGENTS)[0]],
  };
  const skillGroups = isGlobal ? SKILL_GROUPS : projectGroups(SKILL_GROUPS);
  const commandList = isGlobal ? COMMAND_LIST : projectCatalog(COMMAND_LIST);
  const agentList = isGlobal ? AGENT_LIST : projectCatalog(AGENT_LIST);
  const universalPath = isGlobal ? UNIVERSAL_PATH : toProjectPath(UNIVERSAL_PATH);

  const result = await group({
    skills: () => paginatedGroupMultiselect({
      message: 'Select skill directories to link',
      options: annotateGroups(skillGroups, SKILLS_DIR),
      lockedGroups: projUniversalAgents,
      initialValues: linkedValues(skillGroups, SKILLS_DIR),
      required: false,
      maxItems: 10,
    }),
    commands: () => styledMultiselect({
      message: 'Select command directories to link',
      options: annotate(commandList, COMMANDS_DIR),
      initialValues: linkedValues(commandList, COMMANDS_DIR),
      required: false,
    }),
    agents: () => styledMultiselect({
      message: 'Select agent config files to link',
      options: annotate(agentList, AGENTS_FILE),
      initialValues: linkedValues(agentList, AGENTS_FILE),
      required: false,
    }),
  }, {
    onCancel: () => { cancel('Cancelled.'); process.exit(0); },
  });

  const skills = result.skills || [];
  const commands = result.commands || [];
  const agents = result.agents || [];
  const allSkills = [universalPath, ...skills];

  const total = allSkills.length + commands.length + agents.length;
  if (total === 0) { outro('Nothing selected.'); return; }

  // ── Summary ──
  const methodLabel = method === 'symlink' ? 'Symlink' : 'Copy';
  const summaryLines = [];
  if (allSkills.length) {
    summaryLines.push(`Skills (${allSkills.length}):`);
    allSkills.forEach(s => summaryLines.push(`  → ${s}`));
  }
  if (commands.length) {
    if (summaryLines.length) summaryLines.push('');
    summaryLines.push(`Commands (${commands.length}):`);
    commands.forEach(c => summaryLines.push(`  → ${c}`));
  }
  if (agents.length) {
    if (summaryLines.length) summaryLines.push('');
    summaryLines.push(`Agent configs (${agents.length}):`);
    agents.forEach(a => summaryLines.push(`  → ${a}`));
  }
  summaryLines.push('');
  summaryLines.push(`Scope: ${isGlobal ? 'Global' : 'Project'}`);
  summaryLines.push(`Method: ${methodLabel}`);
  summaryLines.push(`Source: ${shorten(DOTFILES_DIR)}`);

  note(summaryLines.join('\n'), 'Installation Summary');

  const proceed = await confirm({ message: 'Proceed with installation?' });
  if (!proceed || typeof proceed === 'symbol') { cancel('Cancelled.'); process.exit(0); }

  // ── Execute ──
  const s = spinner();
  s.start(method === 'symlink' ? 'Creating symlinks...' : 'Copying files...');

  const stats = { created: 0, exists: 0, errors: [] };

  function doInstall(items, target) {
    for (const item of items) {
      try {
        const r = method === 'symlink'
          ? createLink(item, target)
          : createCopy(item, target);
        stats[r === 'created' ? 'created' : 'exists']++;
      } catch (err) {
        stats.errors.push(`${item}: ${err.message}`);
      }
    }
  }

  doInstall(allSkills, SKILLS_DIR);
  doInstall(commands, COMMANDS_DIR);
  doInstall(agents, AGENTS_FILE);
  ensureFrontMatter(COMMANDS_DIR);

  s.stop('Done!');

  const resultLines = [];
  const verb = method === 'symlink' ? 'symlink(s)' : 'copie(s)';
  if (stats.created) resultLines.push(`✓ ${stats.created} new ${verb} created`);
  if (stats.exists) resultLines.push(`✓ ${stats.exists} already linked`);
  if (stats.errors.length) {
    resultLines.push(`✗ ${stats.errors.length} error(s):`);
    stats.errors.forEach(e => resultLines.push(`  ${e}`));
  }

  if (resultLines.length) note(resultLines.join('\n'), 'Results');
  outro('Installation complete!');
}

main().catch(err => {
  cancel(`Error: ${err.message}`);
  process.exit(1);
});
