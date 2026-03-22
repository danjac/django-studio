Look up project documentation by topic, or create it interactively if it doesn't exist.

**Arguments:** `<topic>` — the documentation topic (e.g. `maps`, `payments`, `rss`, `search`)

**Step 1 — Find the document**

Normalize the topic: lowercase, replace spaces with hyphens. List all `.md` files directly under
`docs/` (not subdirectories). Match filenames case-insensitively against the basename without
extension (e.g. `maps` matches `UI-Recipes.md`, `rss-parsing` matches `RSS-Parsing.md`).

- **Exact match** → proceed to Step 2
- **Multiple matches** → list them and ask the user which one they mean, then proceed to Step 2
- **No match** → notify the user ("No `docs/<topic>.md` found."), proceed to Step 3

**Step 2 — Internalize and summarize**

Read the document fully. Present a concise summary to the user covering:

- What the doc is about
- Key patterns and any required settings or config
- Relevant code snippets

Hold the full content in context — you are now ready to apply these patterns without re-reading.
Stop here unless the user asks a follow-up question.

**Step 3 — Create new documentation**

The doc does not exist yet. Notify the user and start an interview to gather what's needed.

Ask questions appropriate to the topic — adapt to what makes sense rather than following a fixed
script. Typical areas to probe (use only what applies):

- What is this feature for, and how is it used in this project?
- Are there model fields, properties, or methods involved?
- Are there settings or CSP changes required?
- Is there a background task, signal, or management command?
- What does the template or UI look like?
- Are there third-party packages involved? Which ones?

Once you have enough information, write the doc following the style and conventions of existing
docs (see `docs/UI-Recipes.md`, `docs/Django.md` as style references). Use the actual project-specific
details — this doc should reflect how this project uses the feature, not a generic how-to.

**Filename convention:** Capital-Kebab-Case.md — capitalise each word, separate with hyphens.
Examples: `docs/UI-Recipes.md`, `docs/RSS-Parsing.md`, `docs/Google-UI-Recipes.md`, `docs/Stripe-Payments.md`.

After writing, remind the user: if this doc would be useful as a built-in template doc for all
projects, use `/djstudio feedback` to propose it.

## Help

```
/djstudio docs <topic>
```

Looks up `docs/<topic>.md` in this project. If found, summarizes it and holds it in context
for use. If not found, interviews you and writes a project-specific doc.

Over time, generated projects accumulate their own `docs/` entries — project-specific integrations,
third-party services, domain patterns — beyond what the template ships. This command makes that
knowledge discoverable and immediately actionable.

**Arguments:**
- `<topic>` — documentation topic (e.g. `maps`, `payments`, `rss`, `search`, `notifications`)

**Examples:**
```
/djstudio docs maps
/djstudio docs payments
/djstudio docs rss
```
