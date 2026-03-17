# Navigation

Templates: `templates/navbar.html`, `templates/sidebar.html`

## Navbar

`navbar.html` is a sticky, responsive site header included in `base.html`. It provides:

- **Site logo** - links to `{% url 'index' %}`
- **User dropdown** - account settings, admin link (staff only), sign out
- **Mobile menu toggle** - hamburger/X button visible on `< md` screens
- **Mobile slide-in nav** - renders `sidebar.html` when a sidebar is present, sign-in/up links otherwise (once sidebar layout is added — see below)
- **Auth links** - sign in / sign up when not authenticated

### How It's Included

`base.html` includes the navbar after the HTMX progress indicator:

```html
{% cookie_banner %}
{% include "navbar.html" %}
```

### AlpineJS State

The navbar component uses a single Alpine scope on the `<header>` element:

```js
{ showMobileMenu: false, showUserDropdown: false }
```

Both panels close whenever the other opens (via `$watch`), and both close on HTMX navigation via `@htmx:before-request.window`.

### Customising the Logo

Replace the text link with an image:

```html
{# In navbar.html, replace the <a> logo element: #}
<a href="{% url 'index' %}" class="flex items-center gap-2">
  <img src="{% static 'img/logo.png' %}" alt="{{ request.site.name }}" class="size-8 rounded-xl">
  <span class="text-lg font-semibold text-zinc-900 dark:text-zinc-100">{{ request.site.name }}</span>
</a>
```

### Customising the Auth Links

When not authenticated, the navbar shows sign-in and sign-up buttons. To add more links (e.g. an "About" page):

```html
{# Add before the {% else %} login block: #}
{% else %}
  <li>
    <a href="{% url 'about' %}" class="text-sm font-semibold text-zinc-600 hover:text-zinc-900 dark:text-zinc-400 dark:hover:text-zinc-100">
      About
    </a>
  </li>
  <li>
    <a href="{% url 'account_login' %}" class="btn btn-secondary">Sign in</a>
  </li>
```

---

## Sidebar

`sidebar.html` is a navigation list used in two places:

1. The **desktop sidebar** (if your layout has one — see [Adding a Sidebar Layout](#adding-a-sidebar-layout) below)
2. The **mobile slide-in menu** inside `navbar.html`

### Default Items

The template ships with two placeholder items (Home, Settings). Replace them with your application's navigation using the `{% partial item %}` shorthand:

```html
{% url 'podcasts:subscriptions' as subscriptions_url %}
{% with icon="rss" label="Subscriptions" url=subscriptions_url %}
  {% partial item %}
{% endwith %}

{% url 'episodes:bookmarks' as bookmarks_url %}
{% with icon="bookmark" label="Bookmarks" url=bookmarks_url %}
  {% partial item %}
{% endwith %}
```

The `item` partial renders a consistent `<li><a>` with icon and label. Resolve the URL before the `{% with %}` block — template tags can't run inside `{% with %}` values.

### Active Item Highlighting

`{% partial item %}` does not support active state. When you need active highlighting, write the link directly using the `active_app` or `active_url` template tags (auto-loaded as builtins):

```html
<ul class="space-y-1">
  <li>
    <a
      href="{% url 'podcasts:subscriptions' %}"
      class="flex items-center gap-3 rounded-lg px-3 py-2 text-sm font-semibold transition-colors {% active_app 'podcasts' %}"
    >
      {% heroicon_mini "rss" class="size-4 shrink-0" aria_hidden="true" %}
      {% translate "Subscriptions" %}
    </a>
  </li>
</ul>
```

| Tag | Matches against | Use for |
|-----|----------------|---------|
| `{% active_app 'app' %}` | `request.resolver_match.app_name` | All pages within an app |
| `{% active_url 'name' %}` | `request.resolver_match.url_name` | A specific named view |

Both tags accept multiple names: `{% active_app 'podcasts' 'episodes' %}` is active on either app.

---

## Adding a Sidebar Layout

By default `base.html` uses a centred single-column layout. When your app has authenticated-only sections, add a two-column sidebar layout for logged-in users and keep the centred layout for anonymous visitors.

### 1. Update `base.html`

Replace the `<main>` block with a conditional driven by a `show_sidebar` context variable. Set it to `True` in any view or context processor that needs the sidebar layout:

```html
{% include "navbar.html" %}
{% if show_sidebar %}
  <div class="flex gap-8 py-8 px-4 mx-auto max-w-7xl sm:px-6 lg:px-8">
    <aside class="hidden w-56 md:block shrink-0">
      <nav class="sticky top-20 p-4 rounded-xl border border-zinc-200 bg-zinc-50 dark:border-zinc-800 dark:bg-zinc-900">
        {% block sidebar %}{% include "sidebar.html" %}{% endblock %}
      </nav>
    </aside>
    <main class="flex-1 min-w-0">
{% else %}
  <main class="py-8 px-4 mx-auto max-w-7xl sm:px-6 lg:px-8">
{% endif %}
{% block content %}{% endblock content %}
{% if show_sidebar %}
    </main>
  </div>
{% else %}
  </main>
{% endif %}
```

The sidebar is hidden on `< md` screens — the mobile menu in `navbar.html` provides navigation on smaller screens.

`show_sidebar` can be set however makes sense for the project — from a view, a context processor, a template tag, or a middleware. A common choice is to tie it to authenticated users, but it could equally apply to a specific section, a staff area, or any other condition.

### 2. Update `navbar.html` mobile menu

When a sidebar is present, make the mobile slide-in menu show `sidebar.html` so mobile users get the same navigation. A `show_sidebar` variable works here too:

```html
<nav x-cloak x-show="showMobileMenu" ...>
  {% if show_sidebar %}
    {% block mobile_nav %}{% include "sidebar.html" %}{% endblock %}
  {% else %}
    <ul class="flex flex-col gap-2">
      <li><a href="{% url 'account_login' %}" class="justify-center w-full btn btn-secondary">{% translate "Sign in" %}</a></li>
      <li><a href="{% url 'account_signup' %}" class="justify-center w-full btn btn-primary">{% translate "Sign up" %}</a></li>
    </ul>
  {% endif %}
</nav>
```

### Section-Specific Sidebar

Override `{% block sidebar %}` in a page template to swap in a different navigation for a section — for example, account settings:

```html
{# templates/account/account_nav.html #}
{% load heroicons i18n %}
<ul class="space-y-1">
  <li>
    <a href="{% url 'index' %}"
       class="flex gap-3 items-center py-2 px-3 text-sm font-semibold rounded-lg transition-colors
              text-muted-700 hover:bg-muted-100 dark:text-muted-200 dark:hover:bg-muted-800">
      {% heroicon_mini "arrow-left" class="size-4 shrink-0" aria_hidden="true" %}
      {% translate "Back to site" %}
    </a>
  </li>
  <li>
    <a href="{% url 'account_email' %}"
       class="flex gap-3 items-center py-2 px-3 text-sm font-semibold rounded-lg transition-colors
              {% if request.resolver_match.url_name == 'account_email' %}bg-primary-50 text-primary-700 dark:bg-primary-950 dark:text-primary-300
              {% else %}text-muted-700 hover:bg-muted-100 dark:text-muted-200 dark:hover:bg-muted-800{% endif %}">
      {% heroicon_mini "envelope" class="size-4 shrink-0" aria_hidden="true" %}
      {% translate "Email" %}
    </a>
  </li>
  {# ... more account links ... #}
</ul>
```

Then in the page template:

```html
{% extends "base.html" %}

{% block sidebar %}{% include "account/account_nav.html" %}{% endblock %}

{% block content %}
  ...
{% endblock content %}
```

No separate base template needed — the same two-column layout renders with a different sidebar.

---

## User Dropdown

The user dropdown is defined inline in `navbar.html`. It opens on button click, closes on outside click, and closes on `Escape`.

### Structure

```html
<!-- Trigger button -->
<button type="button" :aria-expanded="showUserDropdown.toString()" @click="showUserDropdown = !showUserDropdown">
  {% heroicon_mini "user-circle" ... %}
  {{ user.username }}
</button>

<!-- Dropdown panel -->
<div x-cloak x-show="showUserDropdown" x-transition.scale.origin.top>
  <ul role="menu">
    <li><!-- signed in as --></li>
    <li role="menuitem"><a href="{% url 'account_email' %}">Account settings</a></li>
    {% if user.is_staff %}
      <li role="menuitem"><a href="{% url 'admin:index' %}">Site admin</a></li>
    {% endif %}
    <li role="menuitem"><!-- logout form --></li>
  </ul>
</div>
```

### Adding Dropdown Items

Add `<li role="menuitem">` elements before the logout item:

```html
<li role="menuitem">
  <a
    href="{% url 'users:preferences' %}"
    class="flex items-center gap-2 px-4 py-2 text-sm font-semibold text-muted-700 hover:bg-muted-100 dark:text-muted-200 dark:hover:bg-muted-800"
  >
    {% heroicon_mini "adjustments-horizontal" class="size-4 shrink-0" aria-hidden="true" %}
    {% translate "Preferences" %}
  </a>
</li>
```

## Accessibility

- The dropdown `<button>` has `:aria-expanded` bound to the AlpineJS state.
- The dropdown panel has `role="menu"` and items have `role="menuitem"`.
- `Escape` closes both the dropdown and mobile menu via `@keyup.escape.window`.
- The mobile toggle button has `aria-label` for screen readers.
- All interactive elements in the dropdown are keyboard-navigable.
