---
description: Extract strings, translate via Claude, compile .mo catalogue
---

Extract all translatable strings, translate them using Claude, and compile the
message catalogue for the given locale (e.g. `fr`, `fr_CA`, `de`, `es`, `nl`).

Read `docs/localization.md` for details on managing i18n/l10n in Django.

**Prerequisites:**

`gettext` binaries (`xgettext`, `msgfmt`) must be installed.

```bash
# Debian/Ubuntu
sudo apt install gettext
# Fedora/RHEL
sudo dnf install gettext
# macOS
brew install gettext
```

If `gettext` is not available, stop and tell the user to install it first.

---

**Steps:**

### 0 — Detect existing locale

Check whether `locale/<locale>/LC_MESSAGES/django.po` already exists.

- **New locale** — the file does not exist. Run all steps below (1 through 5).
- **Existing locale** — the file already exists. This is a re-run to pick up
  new or changed strings. Skip step 2 (LANGUAGES is already set). In step 3,
  only translate entries where `msgstr` is still empty **or** the entry is
  marked `#, fuzzy` — do not re-translate entries that already have a
  translation.

---

### 1 — Run `makemessages`

```bash
just dj makemessages -l <locale> --no-wrap
```

This creates or updates `locale/<locale>/LC_MESSAGES/django.po`. Django marks
strings that were previously translated but whose source has since changed as
`#, fuzzy`; brand-new strings get an empty `msgstr`. If the directory does not
exist, Django creates it automatically.

---

### 2 — Add locale to LANGUAGES *(new locale only — skip if re-running)*

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

### 2b — Create locale format file *(new locale only — skip if re-running)*

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

### 3 — Translate the `.po` file

Read `locale/<locale>/LC_MESSAGES/django.po`.

**Check the `Plural-Forms` header.** If it is still the default
`nplurals=INTEGER; plural=EXPRESSION;` placeholder, replace it with the
correct rule for `<locale>`. See `resources/plural-forms.md` for the full
reference table. For any locale not listed there, use the GNU gettext manual.

**Translate every entry where `msgstr` is empty** (and any marked `#, fuzzy`).
Use the project name and description (from `cookiecutter.json` or README) as
context so proper nouns and app-specific terminology are translated consistently.

For simple strings:
```
msgid "Save changes"
msgstr "Enregistrer les modifications"
```

For plural strings, fill in all `msgstr[n]` forms:
```
msgid "%(count)s item"
msgid_plural "%(count)s items"
msgstr[0] "%(count)s élément"
msgstr[1] "%(count)s éléments"
```

Remove the `#, fuzzy` flag after translating a fuzzy entry.

Write the updated `.po` file back.

---

### 4 — Compile

```bash
just dj compilemessages
```

This generates `locale/<locale>/LC_MESSAGES/django.mo`.

---

### 5 — Report

Print a summary:

```
Translated: <N> strings  (X new, Y fuzzy updated, Z already had translations)
Locale:     <locale>
Catalogue:  locale/<locale>/LC_MESSAGES/django.mo
```

For a re-run, if N is 0 (no new or fuzzy strings were found), say:

```
No new or changed strings found for <locale>. Catalogue is up to date.
```

If any `msgid` contained Python format specifiers (`%(var)s`, `{var}`), remind
the user to verify that the translated strings preserve them exactly.
