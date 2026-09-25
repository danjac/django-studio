# Testing

This project uses pytest with pytest-django for unit tests and Playwright for E2E tests.

## Contents

- [Test Configuration](#test-configuration)
- [Running Tests](#running-tests)
- [Test Structure](#test-structure)
- [Root conftest.py](#root-conftestpy)
- [Unit Test Fixtures](#unit-test-fixtures)
- [E2E Fixtures](#e2e-fixtures)
- [Recipes](#recipes)
- [Unit Tests](#unit-tests)
- [View Tests with HTMX](#view-tests-with-htmx)
- [E2E Tests](#e2e-tests)
- [Test Settings](#test-settings)
- [N+1 Detection](#n1-detection)
- [Mocking](#mocking)
- [Coverage](#coverage)
- [E2E Selector Rules](#e2e-selector-rules)
- [Troubleshooting](#troubleshooting)
- [When to Use E2E vs Unit Tests](#when-to-use-e2e-vs-unit-tests)

## Test Configuration

Unit tests are configured under `[tool.pytest.ini_options]` in `pyproject.toml`. E2E tests
use `playwright.ini`. Both use `config.settings`, and there is no separate test settings
module. See [Test Settings](conventions.md#test-settings) for how each run is selected
and which environment overrides E2E tests apply.

## Running Tests

```bash
just test                      # Unit tests
just test my_package/users  # Specific module
just tw                        # Watch mode
just test-e2e                  # E2E tests (headless)
just test-e2e-headed          # E2E tests (visible browser)
just playwright-install       # Install Chromium for E2E
```

## Test Structure

Tests are colocated with modules:

```
my_package/
    users/
        models.py
        views.py
        tests/
            __init__.py
            fixtures.py
            recipes.py
            test_models.py
            test_views.py
            test_playwright.py
```

## Root conftest.py

```python
# conftest.py
pytest_plugins = [
    "my_package.tests.fixtures",
    "my_package.tests.e2e_fixtures",
    "my_package.users.tests.fixtures",
]
```

## Unit Test Fixtures

```python
# my_package/tests/fixtures.py
import pytest
from my_package.users.tests.recipes import UserRecipe

@pytest.fixture
def user():
    return UserRecipe.make()
```

## E2E Fixtures

```python
# my_package/tests/e2e_fixtures.py
import pytest
from playwright.sync_api import Page

from my_package.users.tests.recipes import TEST_PASSWORD, make_verified_user

@pytest.fixture
def e2e_user(transactional_db):
    """Verified user for e2e tests."""
    return make_verified_user()

@pytest.fixture
def auth_page(page: Page, e2e_user, live_server) -> Page:
    """Playwright page authenticated as e2e_user."""
    login_url = f"{live_server.url}{reverse('account_login')}"
    page.goto(login_url)
    page.locator('[name="login"]').fill(e2e_user.email)
    page.locator('[name="password"]').fill(TEST_PASSWORD)
    page.get_by_role("button", name="Sign In").click()
    return page
```

## Recipes

Test objects are built with [model-bakery](https://model-bakery.readthedocs.io/).
Each app keeps its recipes in `<app>/tests/recipes.py`.

```python
# my_package/users/tests/recipes.py
from django.contrib.auth.hashers import make_password
from model_bakery.recipe import Recipe, seq

from my_package.users.models import User

TEST_PASSWORD = "testpass"  # noqa: S105

UserRecipe = Recipe(
    User,
    username=seq("user-"),
    email=seq("user-", suffix="@example.com"),
    password=lambda: make_password(TEST_PASSWORD),
)
```

```python
UserRecipe.make()                    # one instance
UserRecipe.make(3)                   # list of three
UserRecipe.make(first_name="Alice")  # override a field
UserRecipe.extend(is_staff=True)     # a named variant
```

**Only declare fields that carry meaning** — a uniqueness constraint, a semantic
default, or a cross-field invariant. Model Bakery fills everything else in from
the field type, so a recipe does not need a line per column.

### Recipe declarations

| Need | Declaration |
|---|---|
| Unique values | `seq("prefix-")`, `seq("prefix-", suffix="@example.com")` |
| Foreign key / one-to-one | `foreign_key(OtherRecipe)`, `foreign_key(OtherRecipe, one_to_one=True)` |
| Many-to-many | `related(OtherRecipe)`, or pass `make_m2m=True` |
| Cycle through choices | any iterator — e.g. `cycle(Status.values)` |
| Deferred value | a zero-argument callable, e.g. `lambda: timezone.now()` |
| Named variant | `BaseRecipe.extend(**overrides)` |

### Gotchas

**Hash passwords lazily.** Test settings override `PASSWORD_HASHERS` to MD5. A
digest built at import time uses the *default* hashers, and `check_password`
then returns `False` under the test hashers — a silent login failure with no
error. Always use `password=lambda: make_password(...)`, never a module-level
`make_password(...)` call.

**Callables receive no arguments.** Model Bakery calls a callable attribute as
`value()`, so it cannot see the other fields being built. There is no
`LazyAttribute` equivalent — derive cross-field values in a helper function
instead:

```python
def make_verified_user(**kwargs: Any) -> User:
    """Create a user with a verified email address."""
    user = UserRecipe.make(**kwargs)
    EmailAddress.objects.create(user=user, email=user.email, verified=True)
    return user
```

**`seq()` counts rows, it does not count calls.** Sequence numbers depend on how
many objects already exist, so they are unique but not contiguous or
predictable. Never assert on a generated value — assert on the field you passed
in explicitly.

**Generated values are random, not realistic.** Model Bakery fills a `CharField`
with a random string, not a plausible name. Pass the value explicitly where a
test needs readable data. If you want plausible values throughout — for demo
fixtures, screenshots, or seed data — add [`faker`](https://faker.readthedocs.io/)
and call it from the recipe:

```bash
uv add --dev faker
```

```python
from faker import Faker

fake = Faker()

CustomerRecipe = Recipe(
    Customer,
    name=fake.name,          # a zero-argument callable — Model Bakery calls it
    email=seq("customer-", suffix="@example.com"),
)
```

Prefer `seq()` over `faker` for anything `unique=True` — faker can repeat values.

## Unit Tests

```python
# my_package/users/tests/test_models.py
import pytest

@pytest.mark.django_db
class TestUser:
    def test_name_returns_first_name(self):
        user = UserRecipe.make(first_name="Alice")
        assert user.name == "Alice"
```

## View Tests with HTMX

```python
# my_package/tests/test_views.py
import pytest
from django.urls import reverse

@pytest.mark.django_db
class TestHome:
    def test_home_view(self, client):
        response = client.get(reverse("home"))
        assert response.status_code == 200

    def test_htmx_request(self, client):
        response = client.get(
            reverse("home"),
            headers={"HX-Request": "true"},
        )
        assert response.status_code == 200
```

## E2E Tests

```python
# my_package/tests/test_playwright.py
import pytest
from playwright.sync_api import Page, expect

@pytest.mark.e2e
@pytest.mark.django_db(transaction=True)
def test_home_page(page: Page, live_server):
    page.goto(f"{live_server.url}/")
    expect(page.locator("h1")).to_contain_text("Welcome")
```

## Test Settings

```python
# my_package/tests/fixtures.py
@pytest.fixture(autouse=True)
def _settings_overrides(settings):
    settings.CACHES = {
        "default": {"BACKEND": "django.core.cache.backends.dummy.DummyCache"}
    }
    settings.TASKS = {
        "default": {"BACKEND": "django.tasks.backends.dummy.DummyBackend"}
    }
    settings.ALLOWED_HOSTS = ["testserver", "localhost"]
    settings.PASSWORD_HASHERS = ["django.contrib.auth.hashers.MD5PasswordHasher"]
```

## N+1 Detection

[django-zeal](https://github.com/taobojlen/django-zeal) detects a relation loaded once per
row. The unit test env in `pyproject.toml` sets `USE_ZEAL=true` and `ZEAL_RAISE=true`, so
an N+1 fails the test with `NPlusOneError`. E2E tests (`playwright.ini`) run with
`USE_ZEAL=false`. `.env.example` sets only `USE_ZEAL=true`, so under `just serve` an N+1
logs a warning with the file and line instead of breaking the page.
The autouse `_zeal` fixture in `my_package/tests/fixtures.py` also covers ORM code
outside requests (model methods, tasks, management commands).

Fix the query rather than silencing the error:

```python
Book.objects.select_related("author")          # ForeignKey / OneToOneField
Book.objects.prefetch_related("tags")          # ManyToMany / reverse ForeignKey
Book.objects.fetch_mode(models.FETCH_PEERS)    # varying relations; see docs/django-models.md
```

For a deliberate per-row lookup, ignore that one relation:

```python
from zeal import zeal_ignore

with zeal_ignore([{"model": "books.Book", "field": "tags"}]):
    ...
```

Zeal also reports a `.get()` repeated from the same line. Django and allauth do this a
fixed number of times per request (session and email address lookups during login), so
those are listed in `ZEAL_ALLOWLIST` in `config/settings.py`. Add an entry there only for
a lookup inside a third-party package; fix N+1s in project code.

## Mocking

Mock at system boundaries only — never mock private methods.

**Rule: do not mock private functions or methods** (names starting with `_`). They are implementation
details. If you need to control behaviour inside a private method, either:

- Intercept the external call the private method makes (HTTP, filesystem, DB), or
- Refactor the private method/function into a public one if it needs independent testing.

| Boundary type          | Tool                           |
| ---------------------- | ------------------------------ |
| Async HTTP (`aiohttp`) | `aioresponses`                 |
| WebSocket consumers    | `channels.testing.WebsocketCommunicator` — see `docs/channels.md` |
| Any callable/module    | `pytest-mock` (`mocker.patch`) |

```python
# BAD: mocks a private implementation detail
def test_version_check(mocker):
    mocker.patch("my_package.management.commands.sync_vendors._latest_github_version",
                 return_value="2.0.0")
    call_command("sync_vendors", "--check")

# GOOD: intercept the HTTP call the private method makes
from aioresponses import aioresponses

def test_version_check():
    with aioresponses() as m:
        m.get("https://api.github.com/repos/owner/repo/releases/latest",
              payload={"tag_name": "v2.0.0"})
        call_command("sync_vendors", "--check")

# GOOD: mock at a public module boundary
def test_external_api(mocker):
    mock = mocker.patch("my_package.client.get_data")
    mock.return_value = {"result": "mocked"}
    # test logic
```

## Coverage

Coverage is reported on every test run (`--cov-report=term-missing`). The 100% gate is commented out in `pyproject.toml` by default - enable it when the project is mature:

```toml
# pyproject.toml
addopts = [
    ...
    "--cov-fail-under=100",  # uncomment to enforce
]
```

## E2E Selector Rules

Page-wide positional selectors (`[x-data] button`, `.relative button`) match the
first element in DOM order, which is usually a navbar or layout component rather
than the one you intend. This makes tests fragile and hard to debug.

**Rules:**

1. **Scope to the component root.** Always start the locator chain from the
   component's stable `id` or `data-component` attribute (see `docs/alpine.md`).

2. **Prefer semantic selectors.** Use `get_by_role` with a `name`, `get_by_label`,
   or `get_by_text` rather than CSS class paths.

3. **Avoid `.first()` and `.nth()` unless the element is a sequence.**
   If you reach for `.first()` to disambiguate, it means your selector is too broad
   — add a scope ancestor instead. When `.first()` is appropriate (e.g.
   the first item in a list), add a comment explaining why.

```python
# BAD: matches the first button on the entire page
page.locator("[x-data] .relative button").first.click()

# GOOD: scoped to the specific component
upload = page.locator("#file-upload")
upload.get_by_role("button", name="Remove file").click()

# GOOD: when targeting a list item, scope to the list then the item
file_list = page.locator("#file-upload [data-file-list]")
file_list.get_by_role("button", name="Remove file").first.click()
# .first() here is intentional — removing the first file from the list
```

## Troubleshooting

### Playwright E2E tests fail with "Target closed" or SIGTRAP on Linux

If Playwright browser launches suddenly start failing, check whether `/tmp` is full:

```bash
df -h /tmp
du -sh /tmp/* 2>/dev/null | sort -rh | head -20
```

On distributions that mount `/tmp` as a tmpfs (e.g. Fedora), pytest temp directories
(`/tmp/pytest-of-$USER`) can grow to fill the available space. Playwright needs `/tmp`
for browser profile directories and downloads.

**Fix:** Remove stale pytest temp files:

```bash
rm -rf /tmp/pytest-of-$USER
```

Then retry `uv run playwright install` if browser binaries were also cleared.

## When to Use E2E vs Unit Tests

**Use E2E (Playwright) for:**

- JavaScript interactivity (Alpine.js)
- HTMX swapping behavior
- Multi-page flows
- Browser-specific behavior

**Use Unit Tests for:**

- Django view logic
- Model methods
- Form validation
- API responses
