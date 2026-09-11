**/dj-localize [locale]**

Extracts translatable strings, translates them with TranslateBot, and compiles
the message catalogue.

**With a locale** — runs the full pipeline for that one language:
  makemessages → translate .po (and model fields) → compilemessages.
  On re-runs, only new or `#, fuzzy` strings are translated.

**Without a locale** — audit + bulk update mode:
  1. Sweeps Python source and Django templates for untranslated user-facing
     strings and fixes them (wraps with `_()` / `{% translate %}`).
  2. Runs the full pipeline for every non-English locale already in LANGUAGES.

Requires:
  - `gettext` binaries (`xgettext`, `msgfmt`)
  - TranslateBot enabled in `.env` (development only):
    `USE_TRANSLATEBOT=true` and `TRANSLATEBOT_API_KEY=<key>`.
    Optionally set `TRANSLATEBOT_MODEL` (default `anthropic/claude-sonnet-5`).

Examples:
  /dj-localize           (audit all source, then update all languages)
  /dj-localize fr
  /dj-localize de
  /dj-localize fr_CA
