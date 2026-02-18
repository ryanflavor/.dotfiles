---
name: mission
description: Coordinate multiple droid agents working in parallel via tmux panes. Use when the user explicitly asks for an "agent team", "mission", "teammates", or when the task requires agents that can see each other's work, communicate directly, share a task list, or when the user wants to observe and steer multiple agents in real-time. Do NOT use for simple parallel tasks where subagents suffice — mission is for persistent, interactive, collaborative teams. Also activates automatically when MISSION_AGENT_NAME environment variable is set (you are a teammate). Do not read mission source code — use the CLI commands below.
---

# Mission — Multi-Agent Collaboration

> All operations use the `mission` CLI. Do not create droid config files or manually operate tmux.

Environment variables `MISSION_TEAM_NAME` and `MISSION_AGENT_NAME` are auto-detected. When set, `-t` and `--from` can be omitted.

## Role Detection

Run `echo $MISSION_AGENT_NAME`:
- **Has output** → You are a **teammate**, skip to Teammate section
- **No output** → You are the **team lead**

---

## Team Lead

When a user describes a task that benefits from parallel work, autonomously:
1. Create a team with a descriptive name based on the task
2. Break the work into tasks
3. Spawn teammates with clear, self-contained prompts
4. Monitor progress and synthesize results
5. Clean up when done

### Commands

```bash
# TeamCreate — create a team
mission create <team-name> -d "description"

# Spawn — start a teammate (prompt delivered via inbox)
mission spawn <agent-name> -t <team> -p "Detailed task instructions. Include all context the agent needs — they don't share your conversation history."

# SendMessage — communicate
mission send <to> "content" -s "summary"                    # direct message
mission send all "content" --type broadcast                  # broadcast (use sparingly)
mission send <agent> "done" --type shutdown_request          # request shutdown

# Read — check inbox
mission read

# Task management
mission task create "subject" -d "description"               # create task
mission task create "integration test" -b "1,2"              # with dependencies
mission task list                                             # list all
mission task get <id>                                         # get details
mission task update <id> -o <agent> -s in_progress           # assign & start

# Observe
mission status                  # team status
mission capture <agent>         # view agent pane output
mission interrupt <agent>       # interrupt agent (Escape)

# TeamDelete — cleanup (shut down teammates first)
mission delete <team-name>
```

### Guidelines

- Give each teammate a **self-contained prompt** with all needed context
- Size tasks so teammates can work **independently** without editing the same files
- Use `mission read` to check for teammate reports
- Use `mission capture` to observe teammate progress
- Shut down teammates before deleting the team

---

## Teammate

When `MISSION_AGENT_NAME` is set. All `-t` and `--from` flags auto-detected.

### On startup

```bash
mission read                    # get your initial task from inbox
```

### Work loop

1. Read task → execute → report results:
   ```bash
   mission send team-lead "results" -s "summary"
   ```
2. Check for more work:
   ```bash
   mission task list
   mission task update <id> -o me -s in_progress    # claim a task
   mission task update <id> -s completed             # mark done
   ```
3. Periodically check inbox:
   ```bash
   mission read
   ```

### Respond to shutdown

```bash
mission send team-lead "done" --type shutdown_response --approve
mission send team-lead "still working" --type shutdown_response --reject
```

### Rules

- Communicate only via `mission send` — text responses are not visible to teammates
- Always respond to shutdown requests
- Do not spawn other droids or modify mission configuration
