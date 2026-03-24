**/dj-create-e2e [<app_name>] <description>**

Writes Playwright E2E tests for a described user interaction.

Asks for authentication requirement (logged-in vs anonymous) if not clear from
the description. Creates or appends to `test_playwright.py` in the app's tests
directory.

Examples:
  /dj-create-e2e store "user adds product to cart and checks out"
  /dj-create-e2e "user resets their password"
