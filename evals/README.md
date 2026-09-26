# Skill evals

End-to-end checks that the `dj-*` skills produce working code in a freshly
generated project. `tests/` checks the scaffold; these check what the skills do to it.

Each run costs tokens and takes several minutes per case, so run it by hand when
changing a skill or the docs a skill relies on. It does not run in CI.

## Running

Requirements: Docker, `just`, `uv`, and the `claude` CLI logged in.

```bash
just eval              # every case
just eval 01 03        # cases whose file name starts with 01 or 03
just eval --keep 02    # keep the generated project to inspect it
just eval --model opus # choose the model for the build and review agents
```

For each case the runner:

1. **Setup:** renders the template into a temp dir, writes `.env` with free host
   ports, runs `just start --wait`, `just install`, `just dj makemigrations users` and
   `just dj migrate`, runs the case's `## Setup` block if there is one, and commits a
   baseline.
2. **Build:** runs the `## Prompt` block with `claude -p` in the project, with
   the plugin loaded (`--plugin-dir plugin`) and permissions skipped (the project
   is a throwaway temp dir). The runner adds a note telling the agent that nobody
   will answer questions.
3. **Check:** runs the `## Check` block with `bash -euo pipefail` in the project.
   It must exit 0. `$EVAL_BUILD_OUTPUT` holds the path to the build agent's final
   message.
4. **Review:** runs the `## Review` block with a fresh `claude -p` limited to
   Read, Grep and Glob, with no settings, MCP servers or build context. The
   runner adds the list of files changed since the baseline, including any the
   build committed, and the standard reviewer rules. The review passes when its
   last line is `No issues found.`

Then it stops the services, removes their volumes and deletes the temp dir.

A case whose prompt starts with `/dj-bootstrap` tests the plugin skill that creates
the project, so the runner skips step 1: it starts the build in an empty directory
and passes free host ports to the build and check phases as environment
variables (`POSTGRES_PORT`, `DATABASE_URL` and so on), which override the `.env`
the skill writes. `{template}` in its prompt becomes the path
of this checkout, so the case tests local changes to the template. The review gets
no changed-file list, since every file is new.

Logs go to `evals/logs/` (gitignored): `<stamp>-<case>.log` for the phases and
`<stamp>-<case>.jsonl` for the build transcript.

## Writing a case

A case is one Markdown file in `cases/`, named `NN-<skill-or-topic>.md`. The
runner reads the first fenced block under each of these headings:

```
# <Title>

<What the case covers.>

## Setup      (optional)
<sh block run before the baseline commit, e.g. to seed code for an audit.>

## Prompt
<The skill invocation, starting with the slash command, followed by every
answer the skill would ask for.>

## Check
<sh block that must exit 0.>

## Review
<Prompt for the reviewer: what to review and a numbered list of facts to verify.>
```

Rules:

- **The prompt answers everything.** Walk through the skill's questions and give
  an answer for each. An unanswered question means the agent picks the default,
  and the case stops testing what you meant.
- **Checks test behaviour, not wording.** Prefer `just check-all`, Django system
  checks and `manage.py shell -c` assertions on the models, forms and URLs over
  grepping source text. Call `uv run python manage.py` directly for multi-line
  `shell -c` code: `just dj` does not quote its arguments.
- **Keep the review short.** List the structural facts to verify. The runner adds
  the standard rules: quote the text read, report only real defects, end with
  `No issues found.` when there are none. Don't list the skill's intentional
  design choices; the rules already keep the reviewer off them.
- **The reviewer never sees the build.** It gets only the changed-file list. An
  audit case may put `{build_output}` in its review prompt to pass the report in.
- **Keep the suite small.** Add a case only when it covers a skill or path no
  other case does.

The generated package is `my_app` (project name "My App").
