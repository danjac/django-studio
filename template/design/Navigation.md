# Navigation

Templates: `templates/navbar.html`, `templates/sidebar.html`

## Navbar

`navbar.html` is a sticky, responsive site header included in `default_base.html`. It provides:

- **Site logo** - links to `{% url 'index' %}`
- **User dropdown** - account settings, admin link (staff only), sign out
- **Mobile menu toggle** - hamburger/X button visible on `< md` screens
- **Mobile slide-in nav** - renders `sidebar.html` content in a slide-down panel
- **Auth links** - sign in / sign up when not authenticated

### How It's Included

`default_base.html` includes the navbar after the HTMX progress indicator:

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

1. The **desktop sidebar** (if your layout has one - see [layout.md](layout.md))
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

The `item` partial is defined at the bottom of `sidebar.html` and renders a consistent `<li><a>` with icon and label.

The URL must be resolved before the `{% with %}` block because template tags can't run inside `{% with %}` values. Use `{% url '...' as var %}` at the top of each item.

### Active Item Highlighting

Use Django's `request.resolver_match` to apply an active state:

```html
<a
  href="{% url 'podcasts:subscriptions' %}"
  class="flex items-center gap-3 rounded-lg px-3 py-2 text-sm font-semibold transition-colors
         {% if request.resolver_match.url_name == 'subscriptions' %}
           bg-indigo-50 text-indigo-700 dark:bg-indigo-950 dark:text-indigo-300
         {% else %}
           text-zinc-700 hover:bg-zinc-100 dark:text-zinc-200 dark:hover:bg-zinc-800
         {% endif %}"
>
  {% heroicon_mini "rss" class="size-4 shrink-0" aria-hidden="true" %}
  Subscriptions
</a>
```

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
    class="flex items-center gap-2 px-4 py-2 text-sm font-semibold text-zinc-700 hover:bg-zinc-100 dark:text-zinc-200 dark:hover:bg-zinc-800"
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
