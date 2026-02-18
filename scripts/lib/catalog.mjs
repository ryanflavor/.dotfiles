export const UNIVERSAL_PATH = '~/.agents/skills';

export const UNIVERSAL_AGENTS = {
  'Universal (.agents/skills)': [
    { label: 'Amp' },
    { label: 'Codex' },
    { label: 'Gemini CLI' },
    { label: 'GitHub Copilot' },
    { label: 'Kimi Code CLI' },
    { label: 'OpenCode' },
  ],
};

export const SKILL_GROUPS = {
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

export const COMMAND_LIST = [
  { value: '~/.claude/commands', label: 'Claude Code (.claude/commands)' },
  { value: '~/.codex/prompts', label: 'Codex (.codex/prompts)' },
  { value: '~/.factory/commands', label: 'Droid (.factory/commands)' },
  { value: '~/.gemini/antigravity/global_workflows', label: 'Gemini CLI (.gemini/global_workflows)' },
];

export const AGENT_LIST = [
  { value: '~/.claude/CLAUDE.md', label: 'Claude Code (CLAUDE.md)' },
  { value: '~/.codex/AGENTS.md', label: 'Codex (AGENTS.md)' },
  { value: '~/.factory/AGENTS.md', label: 'Droid (AGENTS.md)' },
];

export function allSkillPaths() {
  return [
    UNIVERSAL_PATH,
    ...SKILL_GROUPS['Other agents'].map(o => o.value),
  ];
}

export function allCommandPaths() {
  return COMMAND_LIST.map(o => o.value);
}

export function allAgentPaths() {
  return AGENT_LIST.map(o => o.value);
}
