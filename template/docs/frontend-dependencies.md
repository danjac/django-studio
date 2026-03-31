# Frontend Dependencies

This project vendors all frontend JavaScript and CSS files directly into
`static/vendor/` (and `tailwind/` for Tailwind plugins). There is no npm, no
Node.js build step, and no CDN links in production.

Most vendored packages are tracked in `vendors.json` at the project root.
The `sync_vendors` management command checks for updates and downloads them.

Some assets have no versioned releases (e.g. certain HTMX extension plugins).
These can be placed in `static/vendor/` directly — just copy the file manually
and reference it from templates. There is no need to add them to `vendors.json`
since `sync_vendors` would have nothing to check.

## Contents

- [vendors.json format](#vendorsjson-format)
- [Adding a new dependency](#adding-a-new-dependency)
- [Checking for and downloading updates](#checking-for-and-downloading-updates)
- [What goes where](#what-goes-where)

## vendors.json format

Each key is the package name. Two layouts are supported:

### Single file

```json
{
  "htmx": {
    "version": "2.0.7",
    "repo": "bigskysoftware/htmx",
    "source": "https://cdn.jsdelivr.net/npm/htmx.org@{version}/dist/htmx.min.js",
    "dest": "static/vendor/htmx.js"
  }
}
```

| Field | Required | Description |
|-------|----------|-------------|
| `version` | yes | Current pinned version |
| `source` | yes | Download URL — use `{version}` as the placeholder |
| `dest` | yes | Output path relative to the project root |
| `repo` | no | `owner/repo` on GitHub — used to look up the latest release. Omit if the source URL already contains a `github.com/owner/repo` path |

### Multiple files (e.g. DaisyUI ships two `.mjs` files)

```json
{
  "daisyui": {
    "version": "5.5.19",
    "files": [
      {
        "source": "https://github.com/saadeghi/daisyui/releases/download/v{version}/daisyui.mjs",
        "dest": "tailwind/daisyui.mjs"
      },
      {
        "source": "https://github.com/saadeghi/daisyui/releases/download/v{version}/daisyui-theme.mjs",
        "dest": "tailwind/daisyui-theme.mjs"
      }
    ]
  }
}
```

The `repo` field is optional here too; the GitHub owner/repo is inferred from
the first `source` URL if it contains a `github.com/owner/repo` path.

## Adding a new dependency

1. Find the minified release asset URL for the library. Prefer jsDelivr CDN
   URLs for npm packages (`https://cdn.jsdelivr.net/npm/<pkg>@{version}/…`) or
   GitHub release asset URLs for libraries that publish `.mjs` / `.min.js`
   release files.

2. Add an entry to `vendors.json`:

   ```json
   "mylibrary": {
     "version": "1.2.3",
     "source": "https://cdn.jsdelivr.net/npm/mylibrary@{version}/dist/mylibrary.min.js",
     "dest": "static/vendor/mylibrary.js"
   }
   ```

3. Download the file for the pinned version:

   ```bash
   just dj sync_vendors --no-input
   ```

4. Reference the file in your template:

   ```html
   <script src="{% static 'vendor/mylibrary.js' %}" defer></script>
   ```

## Checking for and downloading updates

```bash
just dj sync_vendors           # interactive — prompts before downloading
just dj sync_vendors --check   # report available updates, download nothing
just dj sync_vendors --no-input  # non-interactive — download without prompting
```

Version lookups use the GitHub Releases API. The command checks all packages
in parallel and downloads only those that have a newer release.

## What goes where

| File type | Destination |
|-----------|-------------|
| JavaScript (loaded in HTML) | `static/vendor/` |
| Tailwind CSS plugins (`.mjs`) | `tailwind/` |

Both directories are committed to version control — the vendored files are part
of the project, not build artefacts.
