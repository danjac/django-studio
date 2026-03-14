Extract all translatable strings, translate them using Claude, and compile the
message catalogue for the given locale (e.g. `fr`, `fr_CA`, `de`, `es`, `nl`).

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

### 3 — Translate the `.po` file

Read `locale/<locale>/LC_MESSAGES/django.po`.

**Check the `Plural-Forms` header.** If it is still the default
`nplurals=INTEGER; plural=EXPRESSION;` placeholder, replace it with the
correct rule for `<locale>`:

| Locale | Plural-Forms |
|--------|-------------|
| fr, fr_CA, es, pt, it | `nplurals=2; plural=(n > 1);` |
| de, nl, sv, da, fi, nb | `nplurals=2; plural=(n != 1);` |
| pl | `nplurals=3; plural=(n==1 ? 0 : n%10>=2 && n%10<=4 && (n%100<10 || n%100>=20) ? 1 : 2);` |
| ru, uk | `nplurals=3; plural=(n%10==1 && n%100!=11 ? 0 : n%10>=2 && n%10<=4 && (n%100<10 || n%100>=20) ? 1 : 2);` |

For any locale not listed, use the correct rule from the GNU gettext manual.

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
