#!/usr/bin/env node

import {
  intro, outro, cancel, confirm, text,
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

const REPO_URL = 'https://github.com/notdp/.dotfiles.git';
const IGNORE_DIRS = new Set(['.system', '.git', '.github', '.ruff_cache', 'node_modules']);

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

const UNIVERSAL_PATH = '~/.agents/skills';

const UNIVERSAL_AGENTS = {
  'Universal (.agents/skills)': [
    { label: 'Amp' },
    { label: 'Codex' },
    { label: 'Gemini CLI' },
    { label: 'GitHub Copilot' },
    { label: 'Kimi Code CLI' },
    { label: 'OpenCode' },
  ],
};

const SKILL_GROUPS = {
  'Other agents': [
    { value: '~/.adal/skills', label: 'AdaL (.adal/skills)' },
    { value: '~/.agent/skills', label: 'Antigravity (.agent/skills)' },
    { value: '~/.augment/skills', label: 'Augment (.augment/skills)' },
    { value: '~/.claude/skills', label: 'Claude Code (.claude/skills)' },
    { value: '~/.cline/skills', label: 'Cline (.cline/skills)' },
    { value: '~/.codebuddy/skills', label: 'CodeBuddy (.codebuddy/skills)' },
    { value: '~/.codex/skills', label: 'Codex (.codex/skills)' },
    { value: '~/.commandcode/skills', label: 'Command Code (.commandcode/skills)' },
    { value: '~/.continue/skills', label: 'Continue (.continue/skills)' },
    { value: '~/.crush/skills', label: 'Crush (.crush/skills)' },
    { value: '~/.cursor/skills', label: 'Cursor (.cursor/skills)' },
    { value: '~/.factory/skills', label: 'Droid (.factory/skills)' },
    { value: '~/.gemini/antigravity/skills', label: 'Gemini CLI (.gemini/antigravity/skills)' },
    { value: '~/.goose/skills', label: 'Goose (.goose/skills)' },
    { value: '~/.iflow/skills', label: 'iFlow CLI (.iflow/skills)' },
    { value: '~/.junie/skills', label: 'Junie (.junie/skills)' },
    { value: '~/.kilocode/skills', label: 'Kilo Code (.kilocode/skills)' },
    { value: '~/.kiro/skills', label: 'Kiro CLI (.kiro/skills)' },
    { value: '~/.kode/skills', label: 'Kode (.kode/skills)' },
    { value: '~/.mcpjam/skills', label: 'MCPJam (.mcpjam/skills)' },
    { value: '~/.mux/skills', label: 'Mux (.mux/skills)' },
    { value: '~/.neovate/skills', label: 'Neovate (.neovate/skills)' },
    { value: '~/.openhands/skills', label: 'OpenHands (.openhands/skills)' },
    { value: '~/skills', label: 'OpenClaw (skills)' },
    { value: '~/.pi/skills', label: 'Pi (.pi/skills)' },
    { value: '~/.pochi/skills', label: 'Pochi (.pochi/skills)' },
    { value: '~/.qoder/skills', label: 'Qoder (.qoder/skills)' },
    { value: '~/.qwen/skills', label: 'Qwen Code (.qwen/skills)' },
    { value: '~/.roo/skills', label: 'Roo Code (.roo/skills)' },
    { value: '~/.trae/skills', label: 'Trae (.trae/skills)' },
    { value: '~/.vibe/skills', label: 'Mistral Vibe (.vibe/skills)' },
    { value: '~/.windsurf/skills', label: 'Windsurf (.windsurf/skills)' },
    { value: '~/.zencoder/skills', label: 'Zencoder (.zencoder/skills)' },
  ],
};

const COMMAND_LIST = [
  { value: '~/.claude/commands', label: 'Claude Code (.claude/commands)' },
  { value: '~/.codex/prompts', label: 'Codex (.codex/prompts)' },
  { value: '~/.factory/commands', label: 'Droid (.factory/commands)' },
  { value: '~/.gemini/antigravity/global_workflows', label: 'Gemini CLI (.gemini/global_workflows)' },
];

const AGENT_LIST = [
  { value: '~/.claude/CLAUDE.md', label: 'Claude Code (CLAUDE.md)' },
  { value: '~/.codex/AGENTS.md', label: 'Codex (AGENTS.md)' },
  { value: '~/.factory/AGENTS.md', label: 'Droid (AGENTS.md)' },
];

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

// ── Main ─────────────────────────────────────────────────────

async function main() {
  intro('.dotfiles installer');

  // ── Step 1: Dotfiles directory location ──
  const dirInput = await text({
    message: 'Dotfiles directory?',
    placeholder: '~/.dotfiles',
    defaultValue: '~/.dotfiles',
  });
  if (isCancel(dirInput)) { cancel('Cancelled.'); process.exit(0); }

  const DOTFILES_DIR = expand(dirInput.trim());
  const COMMANDS_DIR = path.join(DOTFILES_DIR, 'commands');
  const SKILLS_DIR = path.join(DOTFILES_DIR, 'skills');
  const AGENTS_FILE = path.join(DOTFILES_DIR, 'agents', 'AGENTS.md');

  // ── Step 2: Initialize if needed ──
  if (needsInit(DOTFILES_DIR)) {
    const wantPresets = await confirm({
      message: 'Install pre-made skills & commands from GitHub?',
    });
    if (isCancel(wantPresets)) { cancel('Cancelled.'); process.exit(0); }

    if (wantPresets) {
      const s = spinner();
      s.start('Cloning repository...');
      try {
        if (fs.existsSync(DOTFILES_DIR)) {
          // Clone to temp, then copy content directories over
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

      // Let user pick which skills to keep
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
          if (!keepSkills.has(s)) {
            fs.rmSync(path.join(SKILLS_DIR, s), { recursive: true, force: true });
          }
        }
      }

      // Let user pick which commands to keep
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
          if (f.endsWith('.md') && f !== '.gitkeep' && !keepCommands.has(f)) {
            fs.unlinkSync(path.join(COMMANDS_DIR, f));
          }
        }
      }
    } else {
      fs.mkdirSync(SKILLS_DIR, { recursive: true });
      fs.mkdirSync(COMMANDS_DIR, { recursive: true });
      fs.mkdirSync(path.dirname(AGENTS_FILE), { recursive: true });
    }
  }

  // Ensure directories exist
  fs.mkdirSync(COMMANDS_DIR, { recursive: true });
  fs.mkdirSync(SKILLS_DIR, { recursive: true });
  fs.mkdirSync(path.dirname(AGENTS_FILE), { recursive: true });

  if (!fs.existsSync(AGENTS_FILE)) {
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

  // ── Step 3+: Select agent paths to link ──
  const result = await group({
    skills: () => paginatedGroupMultiselect({
      message: 'Select skill directories to link',
      options: annotateGroups(SKILL_GROUPS, SKILLS_DIR),
      lockedGroups: UNIVERSAL_AGENTS,
      initialValues: linkedValues(SKILL_GROUPS, SKILLS_DIR),
      required: false,
      maxItems: 12,
    }),
    commands: () => styledMultiselect({
      message: 'Select command directories to link',
      options: annotate(COMMAND_LIST, COMMANDS_DIR),
      initialValues: linkedValues(COMMAND_LIST, COMMANDS_DIR),
      required: false,
    }),
    agents: () => styledMultiselect({
      message: 'Select agent config files to link',
      options: annotate(AGENT_LIST, AGENTS_FILE),
      initialValues: linkedValues(AGENT_LIST, AGENTS_FILE),
      required: false,
    }),
  }, {
    onCancel: () => { cancel('Cancelled.'); process.exit(0); },
  });

  const skills = result.skills || [];
  const commands = result.commands || [];
  const agents = result.agents || [];

  // Universal is always included
  const allSkills = [UNIVERSAL_PATH, ...skills];

  const total = allSkills.length + commands.length + agents.length;
  if (total === 0) {
    outro('Nothing selected.');
    return;
  }

  // ── Summary ──
  const summaryLines = [];
  const fmtPath = (p) => p.replace(os.homedir(), '~');
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
  summaryLines.push(`Target: ${fmtPath(DOTFILES_DIR)}`);

  note(summaryLines.join('\n'), 'Installation Summary');

  const proceed = await confirm({ message: 'Proceed with installation?' });
  if (!proceed || typeof proceed === 'symbol') {
    cancel('Cancelled.');
    process.exit(0);
  }

  // ── Execute ──
  const s = spinner();
  s.start('Creating symlinks...');

  const stats = { created: 0, exists: 0, errors: [] };

  function doLink(items, target) {
    for (const item of items) {
      try {
        const r = createLink(item, target);
        stats[r === 'created' ? 'created' : 'exists']++;
      } catch (err) {
        stats.errors.push(`${item}: ${err.message}`);
      }
    }
  }

  doLink(allSkills, SKILLS_DIR);
  doLink(commands, COMMANDS_DIR);
  doLink(agents, AGENTS_FILE);
  ensureFrontMatter(COMMANDS_DIR);

  s.stop('Done!');

  // ── Results ──
  const resultLines = [];
  if (stats.created) resultLines.push(`✓ ${stats.created} new symlink(s) created`);
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
