# Content Security Policy

The project sends a `Content-Security-Policy` header on every response using
Django's built-in CSP support (`SECURE_CSP` in `config/settings.py`). This doc
explains what the script policy allows, what it costs, and how to tighten it
further if a project needs to.

## Contents

- [Current policy](#current-policy)
- [Inline scripts and nonces](#inline-scripts-and-nonces)
- [Why 'unsafe-eval' is allowed](#why-unsafe-eval-is-allowed)
- [Removing 'unsafe-eval'](#removing-unsafe-eval)
  - [Alpine: the CSP build](#alpine-the-csp-build)
  - [htmx: the hx-csp extension](#htmx-the-hx-csp-extension)
  - [Pitfalls](#pitfalls)
  - [Checklist](#checklist)
- [References](#references)

## Current policy

```python
SCRIPT_SCP = [
    CSP.SELF,
    CSP.NONCE,
    CSP.UNSAFE_EVAL,
    *CSP_SCRIPT_WHITELIST,
]
```

| Source | Allowed | Why |
| --- | --- | --- |
| `'self'` | yes | Vendored and project scripts under `static/` |
| Nonce | yes | Inline `<script>` tags rendered with the per-request nonce |
| `'unsafe-inline'` | **no** | Injected `<script>` tags and `onclick="..."` handlers are blocked |
| `'unsafe-eval'` | yes | Alpine directive expressions and htmx `hx-on:*`, trigger filters and `js:` values |

`style-src` still allows `'unsafe-inline'`; this doc covers `script-src` only.

## Inline scripts and nonces

Every inline `<script>` must carry the nonce, provided by the
`django.template.context_processors.csp` context processor:

```html
<script nonce="{{ csp_nonce }}">
  document.addEventListener('alpine:init', () => { ... });
</script>
```

- `<script src="{% static '...' %}">` needs no nonce.
- `{{ data|json_script:"id" }}` is not executed and needs no nonce.
- Inline event handler attributes (`onclick="..."`) cannot be nonced — use
  Alpine directives (`@click`) instead.
- Django only generates a nonce when a template reads `csp_nonce`, so pages
  without inline scripts pay nothing.

A missing nonce fails in the browser console ("Executing inline script violates
the following Content Security Policy directive…"), not on the server. The E2E
test `test_no_content_security_policy_violations` catches this on the base
template.

## Why 'unsafe-eval' is allowed

`'unsafe-eval'` lets JavaScript compile strings into code (`Function`,
`eval`). Two core parts of the stack rely on it:

- **Alpine (standard build)** compiles every directive expression
  (`x-data`, `@click`, `x-show`, `x-init`, ...) with `Function`.
- **htmx** compiles `hx-on:*` handlers, trigger filters
  (`hx-trigger="click[shiftKey]"`) and `js:` / `javascript:` values
  (e.g. in `hx-vals`, `hx-confirm`) with `Function`/`AsyncFunction`.

**The cost:** nonces stop an attacker who can inject HTML from running an
injected `<script>`, but not from injecting markup that Alpine or htmx will
evaluate — for example `<div x-init="...">` or `<div hx-on:load="...">`. The
first line of defence remains Django's auto-escaping: never render user content
with `|safe` / `mark_safe`, never put user data inside Alpine or htmx expression
attributes, and never use `x-html` with user content.

Removing `'unsafe-eval'` closes that gap, but it is a significant change to how
templates are written. The template keeps it by default; the sections below
describe what removing it involves.

## Removing 'unsafe-eval'

Both Alpine and htmx must be dealt with — removing it for only one of them
gains nothing, since the other still evaluates injected attributes.

### Alpine: the CSP build

Alpine publishes a CSP-compatible build (`@alpinejs/csp`) that parses directive
expressions itself instead of using `Function`.

1. Switch the `alpinejs` entry in `vendors.json` (keep the same `dest`), then run
   `just dj sync_vendors --no-input`:

   ```json
   "alpinejs": {
     "version": "3.17.2",
     "repo": "alpinejs/alpine",
     "source": "https://cdn.jsdelivr.net/npm/@alpinejs/csp@{version}/dist/cdn.min.js",
     "dest": "static/vendor/alpine.js"
   }
   ```

2. Rewrite expressions the CSP build cannot parse. It **supports** property
   access, method calls, assignments, comparison/logical/arithmetic operators,
   ternaries, inline `x-data` objects, `x-model`, `x-for`, `$el`, `$event`.
   It **rejects**:

   - arrow functions: `setTimeout(() => show = false, 4000)`
   - template literals, destructuring and spread: `` `${a}` ``, `[...items]`
   - globals: `document`, `window`, `JSON`, `Math`, `console`, `setTimeout`
   - `x-html`

   In the shipped template this affects `templates/messages.html`
   (`setTimeout` in `x-init`) and `templates/navbar.html` (`$watch` with arrow
   functions). Several examples in `docs/alpine.md` and `docs/ui-recipes.md`
   (e.g. `JSON.parse(document.getElementById(...))`) also need rewriting.

3. Move that logic into registered components, in a static file or a nonced
   inline script. Plain JavaScript inside `Alpine.data()` is unrestricted — only
   directive attribute expressions are parsed:

   ```js
   // static/components.js
   document.addEventListener('alpine:init', () => {
     Alpine.data('message', () => ({
       show: true,
       init() {
         setTimeout(() => { this.show = false; }, 4000);
       },
     }));
   });
   ```

   ```html
   <div x-data="message" x-show="show" role="alert">...</div>
   ```

   Pass server data as component arguments (`x-data="lightbox('photos-data')"`)
   and read `json_script` output inside the component, not in the attribute.

### htmx: the hx-csp extension

There are two choices:

- **Stop using the eval features:** no `hx-on:*`, no trigger filters, no `js:`
  values. Handle htmx events with Alpine listeners
  (`@htmx:after:swap="..."`) or code in a registered component. Nothing else
  changes. Practical only if a project genuinely does not need them.
- **Use htmx's `hx-csp` extension** with `safeEval`, which runs those
  expressions through nonced `<script>` injection instead of `Function`. It
  ships in the `htmx.org` package.

To adopt `hx-csp`:

1. Vendor it alongside htmx (same `repo` and version as the `htmx` entry):

   ```json
   "htmx-ext-csp": {
     "version": "4.0.0",
     "repo": "bigskysoftware/htmx",
     "source": "https://cdn.jsdelivr.net/npm/htmx.org@{version}/dist/ext/hx-csp.js",
     "dest": "static/vendor/hx-csp.js"
   }
   ```

2. Enable it. Upstream shows the config as a meta tag — set the equivalent keys
   in `HTMX_CONFIG` and check the rendered `<meta name="htmx-config">`:

   ```html
   <meta name="htmx-config" content='extensions:"hx-csp",safeEval:true'>
   ```

3. Load `hx-csp.js` after `htmx.js`, and give **both script tags a nonce**. The
   extension reads the page nonce from the first `script[nonce]` element when it
   initialises; the only nonced script in `base.html` is at the bottom of
   `<body>`, so without this the extension finds no nonce and blocks all htmx.

   ```html
   <script src="{% static 'vendor/htmx.js' %}" nonce="{{ csp_nonce }}"></script>
   <script src="{% static 'vendor/hx-csp.js' %}" nonce="{{ csp_nonce }}"></script>
   ```

4. Stamp `hx-nonce` on **every element with `hx-*` attributes**, in full pages
   and in partial responses:

   ```html
   <button hx-post="{% url 'save' %}" hx-nonce="{{ csp_nonce }}">Save</button>
   ```

   The extension compares each element's `hx-nonce` with the page nonce. For
   swapped responses it reads the nonce from the response's CSP header and
   rewrites it to the page nonce (same-origin only), so partials render
   `{{ csp_nonce }}` like any other template.

5. Add `HX-Request-Type` to the `Vary` header (alongside `HX-Request` in
   `HtmxCacheMiddleware`) so full pages and partials are cached separately.

6. Optionally enforce Trusted Types: the extension creates an `htmx` policy, so
   add `require-trusted-types-for 'script'` and `trusted-types htmx` to
   `SECURE_CSP`.

### Pitfalls

- **Missing `hx-nonce` breaks elements quietly.** The extension strips the
  element's `hx-*` attributes and logs
  `htmx: [hx-csp] blocked <tag#id>: no hx-nonce attribute` to the console (and
  fires `htmx:security:strip`). The page still renders; the element just does
  nothing. Every new template, partial, doc example and generator skill has to
  include it.
- **Do not use `hx-nonce:inherited` on `<body>` as a shortcut.** htmx resolves
  `hx-nonce` through normal attribute inheritance, so it does silence the
  errors — but injected markup inside `<body>` inherits the nonce too, which
  removes the protection the extension exists to provide. Stamp each element.
- **Cached markup carries stale nonces.** A nonce is per request; HTML cached
  with `@cache_page` or `{% cache %}` embeds an old one. The extension treats a
  nonce it did not expect as stolen and strips it, leaving the cached elements
  inert. Do not cache rendered htmx markup, or cache data rather than HTML.
- **User data in eval attributes is still unsafe.** `safeEval` changes how
  expressions run, not what they can do. HTML escaping does not neutralise
  JavaScript inside `hx-on:*` or `js:` values.

### Checklist

1. Alpine: switch to the CSP build, rewrite unsupported expressions, move logic
   into `Alpine.data()` components.
2. htmx: remove eval features, or adopt `hx-csp` (vendor, config, nonced script
   tags, `hx-nonce` everywhere, `Vary: HX-Request-Type`).
3. Remove `CSP.UNSAFE_EVAL` from `SCRIPT_SCP` in `config/settings.py`.
4. Update `docs/alpine.md`, `docs/htmx.md`, `docs/ui-recipes.md` and any skill
   that generates Alpine or htmx markup to follow the new rules.
5. Tests: assert `'unsafe-eval'` is absent from `script-src` in the CSP unit
   test, and keep `test_no_content_security_policy_violations` passing. Extend
   E2E coverage to pages that use htmx and Alpine interactions — CSP failures
   only show up in the browser.

## References

- [Django CSP reference](https://docs.djangoproject.com/en/6.1/ref/csp/)
- [Alpine CSP build](https://alpinejs.dev/advanced/csp)
- [htmx hx-csp extension](https://four.htmx.org/extensions/hx-csp/)
- [htmx security docs](https://four.htmx.org/docs/)
