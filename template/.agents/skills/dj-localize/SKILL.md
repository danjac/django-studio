---
description: Add locale formats, extract strings, translate with TranslateBot, compile .mo
---

Extract all translatable strings, translate them with
[TranslateBot](https://translatebot.dev/docs/), and compile the message catalogue
for the given locale (e.g. `fr`, `fr_CA`, `de`, `es`, `nl`).

If no locale is given, **first ask the user** whether they want a full audit of
untranslated strings in the source code, or whether to skip straight to
`makemessages`. If they say skip (or similar), go directly to step B (detect
languages) and then the single-locale pipeline.

Read `docs/localization.md` for details on managing i18n/l10n in Django.

**Prerequisites:**

1. `gettext` binaries (`xgettext`, `msgfmt`) must be installed.

   ```bash
   # Debian/Ubuntu
   sudo apt install gettext
   # Fedora/RHEL
   sudo dnf install gettext
   # macOS
   brew install gettext
   ```

   If `gettext` is not available, stop and tell the user to install it first.

2. TranslateBot must be enabled in `.env`. The package ships as a dev
   dependency but is **disabled by default** — it is never installed or
   configured in production.

   Read `.env` and check for `USE_TRANSLATEBOT=true` and a non-empty
   `TRANSLATEBOT_API_KEY`. **Never print, echo, or log the key.**

   **If `USE_TRANSLATEBOT` is missing or `false`** — offer to enable it:

   > TranslateBot is disabled. Shall I set `USE_TRANSLATEBOT=true` in `.env`?

   If the user agrees, set it (uncommenting the line if needed).

   **If `TRANSLATEBOT_API_KEY` is empty or missing** — you cannot add the key
   yourself. Ask the user to add it:

   > TranslateBot needs an API key for the LLM provider. Add it to `.env` as
   > `TRANSLATEBOT_API_KEY=<key>`, then tell me to continue. The default model
   > is `anthropic/claude-sonnet-5`, so an Anthropic API key works out of the
   > box — set `TRANSLATEBOT_MODEL` to use a different provider.

   Wait for confirmation, re-read `.env` to verify the key is set, and only
   then continue. If the user declines, stop — do not translate `.po` files by
   hand as a fallback.

   `TRANSLATEBOT_MODEL` accepts any
   [LiteLLM model name](https://docs.litellm.ai/docs/providers); the API key
   must match that model's provider.

---

## No-locale mode (no argument given)

When the user runs `/dj-localize` with no locale, perform the audit + bulk
update flow below instead of the single-locale steps.

**Before auditing**, ask the user:

> Do you want a full audit of untranslated strings first, or skip straight to `makemessages`?

- If the user wants the **audit**, proceed with step A.
- If the user wants to **skip**, jump to step B.

### A — Audit source for untranslated strings

**Python files** — search `<package_name>/` for user-facing strings that are
not wrapped in a gettext call (`_()`, `gettext()`, `gettext_lazy()`,
`ngettext()`, `ngettext_lazy()`, `pgettext()`, `pgettext_lazy()`).

Focus on strings that will be shown to end users:

- `verbose_name`, `verbose_name_plural`, `help_text`, `label` in models/forms
- Error messages in `ValidationError`, `forms.ValidationError`
- Flash/status messages passed to `messages.add_message` / `messages.success` etc.
- String literals returned in HTTP responses or passed to `render()` context
  that look like display text (not variable names, URLs, or format keys)

Ignore: string literals that are clearly internal (log messages, variable
names, URL patterns, settings values, migration strings, `__str__` format
strings that are not display labels).

**Django templates** — search all `.html` files under `<package_name>/` and
`templates/` for visible text content that is not inside a
`{% translate %}` / `{% trans %}` tag or a `{% blocktranslate %}` /
`{% blocktrans %}` block.

Ignore: template tags, filter expressions, comments `{# … #}`, attribute
values that are URLs or CSS class names, and any text that is already
wrapped in a translation tag.

**Report findings before making changes:**

```
Untranslated strings found
==========================

Python (N files, M strings):
  <package_name>/models.py:12  verbose_name="Widget"
  <package_name>/forms.py:34   ValidationError("This field is required.")
  …

Templates (N files, M strings):
  templates/base.html:45       "Sign in"
  <package_name>/templates/…:8 "No results found."
  …
```

If no issues are found, print:

```
All user-facing strings are already marked for translation.
```

and jump straight to step B.

**Fix all findings** — wrap each bare string with the appropriate call:

- Python: `_("…")` (import `from django.utils.translation import gettext_lazy as _`
  at the top of the file if not already present; use `gettext_lazy` in
  module-level scope, `gettext` inside functions/methods).
- Templates: `{% translate "…" %}` for inline strings; `{% blocktranslate %}…{% endblocktranslate %}` for multi-word blocks containing variables.

After fixing, print a brief summary:

```
Fixed: N strings across M files.
```

---

### B — Detect current languages

Read `config/settings.py` and extract all locales from `LANGUAGES` (skip
`"en"` — English is the source language and has no `.po` file).

Example: if `LANGUAGES = [("en", "English"), ("fr", "Français"), ("de", "Deutsch")]`,
the target locales are `["fr", "de"]`.

If `LANGUAGES` contains only `"en"` (or is empty), print:

```
No non-English locales configured in LANGUAGES. Nothing to translate.
```

and stop.

---

### C — Run the single-locale pipeline for each locale

For every locale detected in step B, run the single-locale steps below,
treating each as an existing locale (skip steps 2–4). Work through them
sequentially, one locale at a time.

---

## Single-locale mode

### 0 — Detect existing locale

Check whether `locale/<locale>/LC_MESSAGES/django.po` already exists.

- **New locale** — the file does not exist. Run all steps below.
- **Existing locale** — the file already exists. This is a re-run to pick up
  new or changed strings. Skip steps 2–4.

---

### 1 — Run `makemessages`

```bash
just dj makemessages -l <locale>
```

This creates or updates `locale/<locale>/LC_MESSAGES/django.po`. Django marks
strings that were previously translated but whose source has since changed as
`#, fuzzy`; brand-new strings get an empty `msgstr`.

Do not pass `--no-wrap`: TranslateBot rewrites `.po` files with a 79-character
wrap width, so unwrapped output causes noisy diffs on every run.

If the project has JavaScript files with translatable strings, also run:

```bash
just dj makemessages -l <locale> -d djangojs
```

---

### 2 — Add locale to LANGUAGES _(new locale only)_

Open `config/settings.py` and find the `LANGUAGES` list. If `<locale>` is not
already present, add it using the **native name** of the language:

```python
LANGUAGES = [
    ("en", "English"),
    ("<locale>", "<native name>"),  # e.g. ("fr", "Français")
]
```

Common native names: `fr` → Français, `fr_CA` → Français (Canada),
`de` → Deutsch, `es` → Español, `nl` → Nederlands, `pt` → Português,
`it` → Italiano, `pl` → Polski, `sv` → Svenska, `da` → Dansk,
`fi` → Suomi, `nb` → Norsk bokmål.

---

### 3 — Create locale format file _(new locale only)_

Check whether `config/formats/<locale>/` exists.

If it does not, create it:

```bash
mkdir -p config/formats/<locale>
touch config/formats/<locale>/__init__.py
```

Then create `config/formats/<locale>/formats.py`. Use Django's built-in locale
formats for `<locale>` (found at `django/conf/locale/<locale>/formats.py` inside
the installed Django package) as a reference, and write only the overrides that
differ from Django's defaults or that should be project-specific. At minimum,
include `DATE_FORMAT` matching the style used in `config/formats/en/formats.py`.

Example for `fr`:

```python
DATE_FORMAT = "j F Y"
SHORT_DATE_FORMAT = "d/m/Y"
DECIMAL_SEPARATOR = ","
THOUSAND_SEPARATOR = "\xa0"
NUMBER_GROUPING = 3
```

See `docs/localization.md#dates-numbers-and-locale-aware-formatting` for the
full list of available variables.

---

### 4 — django-modeltranslation schema _(new locale only, if installed)_

Check whether `"modeltranslation"` is in `INSTALLED_APPS` in `config/settings.py`.
If it is not, skip this step.

`django-modeltranslation` generates migrations for the new `_<locale>` columns
(e.g. `title_fr`, `body_fr`) when it detects a new entry in `LANGUAGES`:

```bash
just dj makemigrations
just dj migrate
```

`migrate` applies them to every schema automatically (including all tenant
schemas in `django-tenants` projects).

---

### 5 — Translation context file

TranslateBot reads `TRANSLATING.md` from the project root (and optionally from
individual app directories) and sends it to the LLM as context on every run.

If `TRANSLATING.md` does not exist, create it from the project name and
description in `README.md`:

```markdown
# Translation context

<Project name> — <one-line description>.

## Tone

<e.g. Friendly and concise. Use the informal "you" form where the language has one.>

## Terminology

- Keep "<Project name>" untranslated.
- <term>: <preferred translation or "do not translate">
```

Show the file to the user and ask whether to adjust tone or terminology before
translating. Commit it — it keeps translations consistent across runs.

---

### 6 — Translate the `.po` files

```bash
just dj translate --target-lang <locale>
```

TranslateBot translates only entries with an empty `msgstr` or a `#, fuzzy`
flag, clears the fuzzy flag, and preserves placeholders (`%(name)s`, `{0}`,
`%s`) and HTML tags. It processes both `django.po` and `djangojs.po` for every
locale path. Existing translations are never replaced unless `--overwrite` is
passed — only use `--overwrite` if the user explicitly asks to re-translate.

In no-locale mode, omit `--target-lang` to translate every language in
`LANGUAGES` in one run:

```bash
just dj translate
```

If the command fails with an API key or provider error, stop and report it to
the user — do not fall back to translating the `.po` file by hand.

---

### 7 — Review plural forms

Read the `Plural-Forms` header of `locale/<locale>/LC_MESSAGES/django.po`.

If it is still the default `nplurals=INTEGER; plural=EXPRESSION;` placeholder,
replace it with the correct rule for `<locale>`. See
`references/plural-forms.md` for the full reference table. For any locale not
listed there, use the GNU gettext manual.

**If `nplurals` is greater than 2** (e.g. `pl`, `ru`, `uk`, `cs`, `ar`),
TranslateBot fills every `msgstr[n]` for `n ≥ 1` with the same plural form,
which is grammatically wrong for these languages. For every entry with a
`msgid_plural`, rewrite `msgstr[1]` … `msgstr[n]` with the correct form for
each plural category:

```
msgid "%(count)s item"
msgid_plural "%(count)s items"
msgstr[0] "%(count)s element"
msgstr[1] "%(count)s elementy"
msgstr[2] "%(count)s elementów"
```

If `nplurals` is 1 or 2, no review is needed.

---

### 8 — Translate model fields _(if modeltranslation is installed)_

If `"modeltranslation"` is not in `INSTALLED_APPS`, skip this step.

```bash
just dj translate --target-lang <locale> --models
```

TranslateBot discovers every model registered with `django-modeltranslation`,
translates only fields that are empty in `<locale>`, and applies all updates in
a single transaction.

---

### 9 — Compile

```bash
just dj compilemessages
```

This generates `locale/<locale>/LC_MESSAGES/django.mo`.

---

### 10 — Report

Check the catalogue status:

```bash
just dj check_translations
```

This prints untranslated and fuzzy counts for every `.po` file and exits
non-zero if any are incomplete. It is a reporting tool only — it is not part
of `just check-all`.

Print a summary:

```
Locale:     <locale>
Catalogue:  locale/<locale>/LC_MESSAGES/django.mo
Status:     <output of check_translations for this locale>
Plurals:    <reviewed N entries | no review needed>
Models:     <translated | skipped>
```

For a re-run where TranslateBot found nothing to translate, say:

```
No new or changed strings found for <locale>. Catalogue is up to date.
```
