---
description: Schedule a management command as a Kubernetes cron job
---

Schedule a Django management command as a Kubernetes cron job in `helm/site/values.yaml`.

**IMPORTANT: Execute one sub-step at a time. Wait for user confirmation before proceeding to the next sub-step. Do not batch multiple questions or actions into a single response.**

## Required reading

- `docs/cron-jobs.md`
- `docs/python-style-guide.md`

Parse `$ARGUMENTS` as: `<app_name> <command_name>`

---

## Step 1 — Check the command exists

Look for `<package_name>/<app_name>/management/commands/<command_name>.py`.

If the file does not exist, ask:

> `<command_name>` doesn't exist yet in `<app_name>`. Would you like to create it first?
> (`/dj-create-command <app_name> <command_name>`)

Wait for the user's answer. Do not proceed with the cron entry until the command exists.

---

## Step 2 — Check for command arguments

Read `<package_name>/<app_name>/management/commands/<command_name>.py` and check
whether it defines `add_arguments`. If it does, list the available arguments and ask:

> `<command_name>` accepts arguments: `<list them>`.
> Which arguments (if any) should be passed in the cron job?
> Leave blank to run with no arguments.

Wait for the answer before proceeding.

---

## Step 3 — Check for existing cron entries

Scan `helm/site/values.yaml` for any `cronjobs:` entries whose `command` field
contains `<command_name>`.

If one or more exist, show them and ask:

> A cron job for `<command_name>` already exists:
>
> ```yaml
> <existing_key>:
>   schedule: "<existing_schedule>"
>   command: "<existing_command>"
> ```
>
> Would you like to:
> 1. Update the schedule of the existing entry
> 2. Add a new entry (e.g. same command, different time)

Wait for the answer and follow the chosen path. If updating, edit the existing
entry's `schedule` field only — do not change the key name or command.

---

## Step 4 — Ask for the schedule

Ask:

> When should `<command_name>` run? Describe in plain English, for example:
> "Every day at 3 AM", "Every 15 minutes", "Every Tuesday at 10 AM UTC".

Wait for the answer, then convert it to a cron expression (five fields, UTC).
Show your working:

```
"Every Tuesday at 10 AM UTC"  →  0 10 * * 2
```

State any assumptions (e.g. "I'm assuming UTC — correct me if you want a different
timezone"). If the description is ambiguous, ask a follow-up before generating.

---

## Step 5 — Confirm the plan

Show the proposed entry and wait for "yes":

```yaml
cronjobs:
  <key>:
    schedule: "<cron_expression>"
    command: "./manage.sh <command_name> <args>"
```

**Key name convention:** `<app_name>-<command_name_kebab>` in lowercase kebab-case
(e.g. `orders-process-pending-orders`). When adding a second entry for the same
command, append a distinguishing suffix (e.g. `-tuesday`, `-weekly`). Suggest a
name and let the user confirm.

Omit `<args>` from the `command:` field if no arguments were requested in Step 2.

---

## Step 6 — Write the entry

Open `helm/site/values.yaml` and:

- **New entry:** append under the `cronjobs:` key. Do not modify any other entries.
- **Update:** change the `schedule:` field of the existing entry only.

---

## Step 7 — Verify

```bash
just check-all
```

---

## Step 8 — Prompt to deploy

Check whether `helm/site/values.secret.yaml` exists (indicating the project has
already been deployed to production).

If it does not exist, no action needed here — the cron job will be created when
the project is first deployed via `/dj-launch`.

If it exists, check whether the management command is a **custom project command**
or a **third-party command**:

- **Custom project command** — file exists at
  `<package_name>/<app_name>/management/commands/<command_name>.py`:

  Ask the user to commit and push the change (or offer to do it for them), then
  ask how they want to deploy:

  > How would you like to deploy?
  > 1. **Deploy through CI** — `just gh deploy` (recommended: builds a fresh Docker
  >    image containing the new command, then runs `helm upgrade` atomically)
  > 2. **Deploy config immediately** — `just deploy-config` (applies the Helm chart
  >    now, but the command must already be in the running container image)

  Recommend option 1 unless the user has a reason to skip CI.

  If GitHub Actions secrets haven't been set up yet (or have changed), remind the
  user to run `just gh-set-secrets` before deploying.

- **Third-party command** — no project file (the command is already in the
  container image via an installed package):

  > The command is provided by a third-party package already in the container
  > image — no new build is needed. Run:
  > ```bash
  > just deploy-config
  > ```
  > This applies the updated `values.yaml` directly via `helm upgrade` without
  > triggering a full CI build.
