# Static Files

This project serves static files directly from Django via WhiteNoise, with Cloudflare acting
as the CDN in front. No separate static file server (Nginx, S3) is needed.

References:
- [WhiteNoise documentation](https://whitenoise.readthedocs.io/en/latest/)
- [Cloudflare CDN reference architecture](https://developers.cloudflare.com/reference-architecture/architectures/cdn/)

User-uploaded files (media) are separate — see `docs/file-storage.md`.

---

## Architecture

```
Browser → Cloudflare CDN → WhiteNoise (Django process)
              ↑
         cache hit: served from Cloudflare edge
         cache miss: fetched from origin, cached for next request
```

WhiteNoise handles serving and compression. Cloudflare handles edge caching and global
distribution. The two work together because WhiteNoise sets the right `Cache-Control`
headers and content-hashed URLs that Cloudflare understands.

---

## How Content Hashing Makes It Work

`CompressedManifestStaticFilesStorage` rewrites static filenames at `collectstatic` time:

```
app.css  →  app.a3f1c9.css
app.js   →  app.d7b2e4.js
```

WhiteNoise then serves those hashed files with:

```
Cache-Control: max-age=31536000, public, immutable
```

Cloudflare caches them at the edge for up to one year. When you deploy new assets:

- The hash changes → the URL changes → Cloudflare treats it as a new resource
- **No manual CDN purge needed** — stale assets are never served

The unhashed URL (`/static/app.css`) redirects to the hashed URL, so any hard-coded
references still work — they just won't be cached long-term.

---

## Settings

```python
# config/settings.py

STATIC_URL = env("STATIC_URL", default="/static/")
STATIC_ROOT = BASE_DIR / "staticfiles"
STATICFILES_DIRS = [BASE_DIR / "static"]

if env.bool("USE_COLLECTSTATIC", default=True):
    STORAGES = {
        "staticfiles": {
            "BACKEND": "whitenoise.storage.CompressedManifestStaticFilesStorage",
        },
    }
else:
    # Development: skip hashing, use runserver_nostatic
    INSTALLED_APPS += ["whitenoise.runserver_nostatic"]
```

`STATIC_URL` defaults to `/static/`. Cloudflare proxies requests to your origin and
caches the responses. You can optionally point `STATIC_URL` to a dedicated subdomain
(e.g. `https://static.example.com/`) — set it via the `STATIC_URL` environment variable
in your Helm values.

---

## Development

In `.env`, `USE_COLLECTSTATIC=false` is set by default. This skips
`CompressedManifestStaticFilesStorage` (no hashing) and adds `whitenoise.runserver_nostatic`
so Django's `runserver` serves raw static files without the full WhiteNoise pipeline.

---

## Deployment

`collectstatic` runs during the Docker image build:

```dockerfile
RUN uv run python manage.py collectstatic --no-input
```

The hashed files are baked into the image. There is no separate step needed at deploy time.

---

## Cloudflare Caching

Cloudflare's default "Standard" cache level caches static file extensions (`.css`, `.js`,
`.png`, etc.) automatically. WhiteNoise's `max-age=31536000, immutable` header tells
Cloudflare to cache for the maximum duration.

First request to a Cloudflare edge node: cache miss → fetched from origin → cached.
Subsequent requests: served from the edge without hitting your server.

If you ever need to force a cache purge (e.g. for an emergency hotfix without a full
deploy), use the Cloudflare dashboard: **Caching → Cache Purge → Purge by URL**.
