# Testing

This project uses pytest with pytest-django for unit tests and Playwright for E2E tests.

## Test Configuration

```ini
# playwright.ini (for E2E tests)
[pytest]
DJANGO_SETTINGS_MODULE = config.settings
asyncio_mode = auto
addopts = -v -x --tb=short -p no:warnings --browser chromium -m e2e
testpaths = myapp
env =
    DJANGO_ALLOW_ASYNC_UNSAFE=true
    USE_CONNECTION_POOL=false
    USE_COLLECTSTATIC=false
    USE_HTTPS=false
    USE_X_FORWARDED_HOST=false
```

```python
# pyproject.toml
[tool.pytest.ini_options]
DJANGO_SETTINGS_MODULE = "config.settings"
asyncio_mode = "auto"
addopts = [
    "-v", "-x", "-p no:warnings", "--ff",
    "--cov", "--reuse-db", "--cov-fail-under=100",
]
markers = ["e2e: end-to-end browser tests with Playwright"]
```

## Running Tests

```bash
just test                      # Unit tests
just test myapp/users  # Specific module
just tw                        # Watch mode
just test-e2e                  # E2E tests (headless)
just test-e2e-headed          # E2E tests (visible browser)
just playwright-install       # Install Chromium for E2E
```

## Test Structure

Tests are colocated with modules:

```
myapp/
    users/
        models.py
        views.py
        tests/
            __init__.py
            fixtures.py
            factories.py
            test_models.py
            test_views.py
            test_playwright.py
```

## Root conftest.py

```python
# conftest.py
pytest_plugins = [
    "myapp.tests.fixtures",
    "myapp.tests.e2e_fixtures",
    "myapp.users.tests.fixtures",
]
```

## Unit Test Fixtures

```python
# myapp/tests/fixtures.py
import pytest
from myapp.users.tests.factories import UserFactory

@pytest.fixture
def user():
    return UserFactory()
```

## E2E Fixtures

```python
# myapp/tests/e2e_fixtures.py
import pytest
from playwright.sync_api import Page

@pytest.fixture
def e2e_user(transactional_db):
    """Verified user for e2e tests."""
    user = UserFactory()
    EmailAddress.objects.create(user=user, email=user.email, verified=True)
    return user

@pytest.fixture
def auth_page(page: Page, e2e_user, live_server) -> Page:
    """Playwright page authenticated as e2e_user."""
    login_url = f"{live_server.url}{reverse('account_login')}"
    page.goto(login_url)
    page.locator('[name="login"]').fill(e2e_user.username)
    page.locator('[name="password"]').fill("testpass")
    page.get_by_role("button", name="Sign In").click()
    return page
```

## Factories

```python
# myapp/users/tests/factories.py
from factory import django
from factory.declarations import Sequence
from myapp.users.models import User

class UserFactory(django.DjangoModelFactory):
    class Meta:
        model = User

    username = Sequence(lambda n: f"user-{n}")
    email = Sequence(lambda n: f"user-{n}@example.com")
    password = django.Password("testpass")
```

## Unit Tests

```python
# myapp/users/tests/test_models.py
import pytest

@pytest.mark.django_db
class TestUser:
    def test_name_returns_first_name(self):
        user = UserFactory(first_name="Alice")
        assert user.name == "Alice"
```

## View Tests with HTMX

```python
# myapp/tests/test_views.py
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
# myapp/tests/test_playwright.py
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
# myapp/tests/fixtures.py
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

## Mocking

```python
def test_external_api(mocker):
    mock = mocker.patch("myapp.client.get_data")
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
