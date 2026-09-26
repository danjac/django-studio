# Plural-Forms reference

Use these values for the `Plural-Forms` header in `.po` files.
For any locale not listed, look up the correct rule in the GNU gettext manual.

| Locale | Plural-Forms |
|--------|-------------|
| `fr`, `fr_CA`, `es`, `pt`, `it` | `nplurals=2; plural=(n > 1);` |
| `de`, `nl`, `sv`, `da`, `fi`, `nb` | `nplurals=2; plural=(n != 1);` |
| `pl` | `nplurals=3; plural=(n==1 ? 0 : n%10>=2 && n%10<=4 && (n%100<10 \|\| n%100>=20) ? 1 : 2);` |
| `ru`, `uk` | `nplurals=3; plural=(n%10==1 && n%100!=11 ? 0 : n%10>=2 && n%10<=4 && (n%100<10 \|\| n%100>=20) ? 1 : 2);` |
| `ar` | `nplurals=6; plural=(n==0 ? 0 : n==1 ? 1 : n==2 ? 2 : n%100>=3 && n%100<=10 ? 3 : n%100>=11 ? 4 : 5);` |
| `cs`, `sk` | `nplurals=3; plural=(n==1) ? 0 : (n>=2 && n<=4) ? 1 : 2;` |
| `ja`, `ko`, `zh`, `tr`, `id` | `nplurals=1; plural=0;` |
