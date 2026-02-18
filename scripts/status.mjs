#!/usr/bin/env node

import { intro, outro, note } from '@clack/prompts';
import { allSkillPaths, allCommandPaths, allAgentPaths } from './lib/catalog.mjs';
import pc from 'picocolors';
import fs from 'node:fs';
import os from 'node:os';
import path from 'node:path';

const HOME = os.homedir();
const expand = (s) => (s === '~' ? HOME : s.startsWith('~/') ? path.join(HOME, s.slice(2)) : s);

const DOTFILES_DIR = expand(process.env.DOTFILES_DIR || '~/.dotfiles');
const COMMANDS_DIR = path.join(DOTFILES_DIR, 'commands');
const SKILLS_DIR = path.join(DOTFILES_DIR, 'skills');
const AGENTS_FILE = path.join(DOTFILES_DIR, 'agents', 'AGENTS.md');

function checkLink(rawPath, expectedTarget) {
  const full = expand(rawPath);
  try {
    const stat = fs.lstatSync(full);
    if (stat.isSymbolicLink()) {
      const target = fs.readlinkSync(full);
      if (target === expectedTarget) return { status: 'linked', target };
      return { status: 'other', target };
    }
    if (stat.isDirectory()) return { status: 'dir' };
    return { status: 'file' };
  } catch { return { status: 'missing' }; }
}

const shorten = (s) => s.replace(HOME, '~');

function formatSection(results) {
  const maxLen = Math.max(...results.map(r => r.path.length));
  return results.map(r => {
    const padded = r.path.padEnd(maxLen);
    switch (r.status) {
      case 'linked':  return `${pc.green('✓')} ${padded} ${pc.dim('→')} ${pc.dim(shorten(r.target))}`;
      case 'other':   return `${pc.yellow('⚠')} ${padded} ${pc.dim('→')} ${pc.yellow(shorten(r.target))}`;
      case 'dir':     return `${pc.dim('○')} ${padded} ${pc.dim('(standalone dir)')}`;
      case 'file':    return `${pc.dim('○')} ${padded} ${pc.dim('(standalone file)')}`;
      case 'missing': return `${pc.dim('✗')} ${pc.dim(padded)}`;
    }
  });
}

function checkSection(paths, expectedTarget) {
  return paths.map(p => {
    const result = checkLink(p, expectedTarget);
    return { path: p, ...result };
  }).filter(r => r.status !== 'missing');
}

intro('.dotfiles status');

const sections = [
  { title: 'Skills', results: checkSection(allSkillPaths(), SKILLS_DIR) },
  { title: 'Commands', results: checkSection(allCommandPaths(), COMMANDS_DIR) },
  { title: 'Agents', results: checkSection(allAgentPaths(), AGENTS_FILE) },
];

let totalLinked = 0;
let totalAll = 0;

for (const section of sections) {
  const lines = formatSection(section.results);
  const linked = section.results.filter(r => r.status === 'linked').length;
  totalLinked += linked;
  totalAll += section.results.length;
  note(lines.join('\n'), `${section.title} (${linked}/${section.results.length})`);
}

outro(`${totalLinked}/${totalAll} linked`);
