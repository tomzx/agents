---
name: llm-automation
description: Prepares and launches an unattended LLM task that runs autonomously while you are away, storing progress and results for review on return.
argument-hint: "<task description>"
---

AUTOMATION_DIR=!`scripts/get-env AUTOMATION_DIR 2>/dev/null || echo "${HOME}/.claude/automation"`
TASK_ID=!`date +%Y%m%d-%H%M%S`
NOW=!`date +%Y-%m-%dT%H:%M:%S`
WORK_DIR=!`pwd`

# LLM Automation

Sets up and launches an autonomous Claude Code task that runs without supervision. Produces a task specification, a self-contained prompt, a run script, and instructions for reviewing results on return.

## Prerequisites

- Claude Code CLI (`claude`) installed and authenticated
- Working directory is the root of the target repository
- Optional: `AUTOMATION_DIR` in `.env` for storing task files (defaults to `~/.claude/automation`)

## Steps

### 1. Clarify the Task

If a task description was not provided as `$1`, ask the user in a single message:

1. What is the goal? (What should be accomplished?)
2. What are the constraints? (What must NOT be done, e.g., "do not push to main", "only touch files in src/", "stop after 50 files")
3. What does success look like? (How will you know it worked?)
4. Which directory should the task run in? (Default: `{WORK_DIR}`)
5. When should it run? (Now in background, at a specific time, or dry run only?)

Record all answers before proceeding. Do not make assumptions about constraints or scope -- these are the most important part of an unattended task.

### 2. Build the Task Specification

Create the automation directory if it does not exist:
```
mkdir -p {AUTOMATION_DIR}
```

Write the task specification to `{AUTOMATION_DIR}/{TASK_ID}.task.md`:

```markdown
---
id: {TASK_ID}
created_at: {NOW}
status: pending
work_dir: <absolute path>
---

# Task: <one-line goal summary>

## Goal

<full description of what to accomplish>

## Constraints

- <constraint 1>
- <constraint 2>

## Success Criteria

- [ ] <criterion 1>
- [ ] <criterion 2>
```

### 3. Construct the Autonomous Prompt

Write the prompt to `{AUTOMATION_DIR}/{TASK_ID}.prompt.txt`.

A good autonomous prompt:

- States the goal precisely with no open questions
- Lists every constraint as an explicit "do not" rule
- Instructs the LLM to note ambiguities in the result file and skip rather than stall
- Ends with this instruction:

  > When finished, write a result summary to `{AUTOMATION_DIR}/{TASK_ID}.result.md` with these sections:
  > - **Done**: what was completed
  > - **Skipped**: what was skipped or blocked, and why
  > - **Success Criteria**: for each criterion, whether it was met (yes/partial/no) and a brief note

If the user supplied `$1` as a short description, expand it into a full autonomous prompt. Do not leave anything underspecified that would require asking a question mid-task.

### 4. Create the Run Script

Write `{AUTOMATION_DIR}/{TASK_ID}.run.sh`:

```bash
#!/usr/bin/env bash
set -euo pipefail

TASK_ID="{TASK_ID}"
AUTOMATION_DIR="{AUTOMATION_DIR}"
WORK_DIR="<absolute working directory>"
LOG_FILE="${AUTOMATION_DIR}/${TASK_ID}.log"
PROMPT_FILE="${AUTOMATION_DIR}/${TASK_ID}.prompt.txt"

mkdir -p "${AUTOMATION_DIR}"
cd "${WORK_DIR}"

echo "[$(date -Iseconds)] Starting task ${TASK_ID}" | tee -a "${LOG_FILE}"

claude -p "$(cat "${PROMPT_FILE}")" 2>&1 | tee -a "${LOG_FILE}"

echo "[$(date -Iseconds)] Task ${TASK_ID} complete" | tee -a "${LOG_FILE}"
```

Make it executable:
```
chmod +x {AUTOMATION_DIR}/{TASK_ID}.run.sh
```

### 5. Launch the Task

Based on the user's answer from step 1:

**Run now (background):**
```bash
nohup {AUTOMATION_DIR}/{TASK_ID}.run.sh > /dev/null 2>&1 &
echo "Task {TASK_ID} launched. PID: $!"
```

**Schedule with `at` (one-time):**
```bash
echo "{AUTOMATION_DIR}/{TASK_ID}.run.sh" | at <time>
# Example times: 22:00, "11pm", "tomorrow 08:00"
```

**Schedule with cron (recurring):**
```
crontab -e
# Add: <cron expression> {AUTOMATION_DIR}/{TASK_ID}.run.sh >> {AUTOMATION_DIR}/{TASK_ID}.log 2>&1
```

**Dry run (inspect without running):**
Print the contents of the prompt file and all created file paths. Do not execute the script.

### 6. Confirm and Summarize

Print the following after setup:

```
Task {TASK_ID} is set up.

Files:
  Spec:    {AUTOMATION_DIR}/{TASK_ID}.task.md
  Prompt:  {AUTOMATION_DIR}/{TASK_ID}.prompt.txt
  Script:  {AUTOMATION_DIR}/{TASK_ID}.run.sh
  Log:     {AUTOMATION_DIR}/{TASK_ID}.log
  Results: {AUTOMATION_DIR}/{TASK_ID}.result.md  (written on completion)

To watch progress:
  tail -f {AUTOMATION_DIR}/{TASK_ID}.log

To review results on return:
  cat {AUTOMATION_DIR}/{TASK_ID}.result.md

To stop the task early:
  kill $(pgrep -f "{TASK_ID}")
```

## Output Format

Print only the confirmation block above after setup. Do not wait for the task to complete.

## Example Usage

**Scenario 1: Overnight refactor**
```
/llm-automation "Refactor all files in src/db/ to use the connection pool. Do not change public APIs. Run tests after each file. Stop after 2 hours."
```
Skill expands the description into a full prompt, creates a run script, and launches it in the background. User returns to `result.md` in the morning.

**Scenario 2: Scheduled standup prep**
```
/llm-automation "Generate a standup summary from git log --since yesterday --all-branches and write it to notes/standup-today.md"
```
User chooses `at 07:30` so the summary is ready before their standup.

**Scenario 3: Batch test generation with a scope limit**
```
/llm-automation "For every function in src/ with no corresponding test in tests/, add a green-path test. Stop after 20 functions."
```
Constraint includes a volume limit to prevent runaway execution. The LLM notes how many it completed in `result.md`.

**Scenario 4: Dry run to review the prompt before committing**
```
/llm-automation "Clean up all TODO comments in the codebase, replacing each with a GitHub issue reference"
```
User chooses dry run to read the generated prompt and verify the scope before launching.

## Useful Commands Reference

| Command | Description |
|---|---|
| `claude -p "<prompt>"` | Run Claude in non-interactive mode |
| `nohup <cmd> &` | Run a command detached from the terminal |
| `tail -f <logfile>` | Stream a log file as it grows |
| `at <time>` | Schedule a one-time command (e.g., `at 22:00`) |
| `atq` | List pending `at` jobs |
| `atrm <job>` | Remove a pending `at` job |
| `crontab -e` | Edit the recurring cron schedule |
| `pgrep -a claude` | List running Claude processes |
| `kill $(pgrep -f "<task-id>")` | Stop a specific running task |
