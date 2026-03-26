**/dj-translate [locale]**

Extracts translatable strings, translates them with Claude, and compiles the
message catalogue.

**With a locale** — runs the full pipeline for that one language:
  makemessages → translate .po → compilemessages.
  On re-runs, only new or `#, fuzzy` strings are translated.

**Without a locale** — audit + bulk update mode:
  1. Sweeps Python source and Django templates for untranslated user-facing
     strings and fixes them (wraps with `_()` / `{% translate %}`).
  2. Runs the full pipeline for every non-English locale already in LANGUAGES.

Requires `gettext` binaries (`xgettext`, `msgfmt`).

Examples:
  /dj-translate           (audit all source, then update all languages)
  /dj-translate fr
  /dj-translate de
  /dj-translate fr_CA
