**/dj-translate <locale>**

Extracts translatable strings, translates them with Claude, and compiles the
message catalogue for the given locale.

Requires `gettext` binaries (`xgettext`, `msgfmt`). On re-runs, only new or
`#, fuzzy` strings are translated — existing translations are preserved.

Examples:
  /dj-translate fr
  /dj-translate de
  /dj-translate fr_CA
