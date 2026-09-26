# CRUD views for a new model

Covers `/djs-create-crud`, including its hand-off to `/djs-create-app` and
`/djs-create-model` when neither the app nor the model exists.

## Prompt

```text
/djs-create-crud catalog Product

Neither the `catalog` app nor the `Product` model exists yet. Follow the skill's
Step 0: create the app, then the model, then the CRUD views.

Answers for djs-create-model:

- Primary key: use the default.
- Timestamps: yes, with the default names `created` / `updated`.
- Fields, in this order:
  - `name`: CharField, max_length 100.
  - `sku`: CharField, max_length 20, unique.
  - `price`: DecimalField, max_digits 10, decimal_places 2. Do not use MoneyField.
  - `in_stock`: BooleanField, default True.
- No extra indexes, no extra uniqueness, no help text, no extra non-editable fields.
- verbose_name "product", verbose_name_plural "products".
- `__str__` returns the name.
- Approve the model sketch as shown.
- Register the model in the admin: no.
- Run migrate: yes.
- Generate CRUD views: yes (this is the CRUD run).

Answers for djs-create-crud:

- The form exposes `name`, `sku`, `price` and `in_stock`.
- URL prefix `products/`.
```

## Check

```sh
just check-all
just dj makemigrations --check --dry-run
for template in list detail form confirm_delete; do
  test -f "templates/catalog/product_${template}.html"
done
if grep -q '__all__' my_app/catalog/forms.py; then
  echo "ProductForm uses fields = __all__"; exit 1
fi
uv run python manage.py shell -c '
from django.test import Client
from django.urls import reverse

from my_app.catalog.forms import ProductForm

assert set(ProductForm._meta.fields) == {"name", "sku", "price", "in_stock"}

client = Client()
for name in ("list", "create"):
    url = reverse(f"catalog:product_{name}")
    assert "/products/" in url, url
    response = client.get(url, HTTP_HOST="localhost")
    assert response.status_code == 302, (url, response.status_code)
for name in ("detail", "edit", "delete"):
    reverse(f"catalog:product_{name}", args=[1])
print("crud assertions passed")
'
# Delete through the confirm page the way htmx does: send the hx-headers the page
# renders, with CSRF enforced (the test client skips CSRF checks by default).
uv run python manage.py shell -c '
import html
import json
import re
import uuid
from decimal import Decimal

from django.test import Client
from django.urls import reverse

from my_app.catalog.models import Product
from my_app.users.models import User

suffix = uuid.uuid4().hex[:8]
user = User.objects.create_user(f"eval-{suffix}", f"eval-{suffix}@example.com", "x")
product = Product.objects.create(name="Widget", sku=f"EV-{suffix}", price=Decimal("1.00"))
url = reverse("catalog:product_delete", args=[product.pk])

client = Client(enforce_csrf_checks=True, HTTP_HOST="localhost")
client.force_login(user)
page = client.get(url)
assert page.status_code == 200, page.status_code
content = page.content.decode()
# Headers htmx sends with the delete: those on the hx-delete element itself plus
# any hx-headers:inherited. Other elements (e.g. the cookie banner) do not count.
button = re.search(r"<[^<>]*\bhx-delete=[^<>]*>", content)
assert button, "no hx-delete element on the confirm page"
attrs = re.findall(r"hx-headers=\x27([^\x27]*)\x27", button.group(0))
attrs += re.findall(r"hx-headers:inherited=\x27([^\x27]*)\x27", content)
headers = {}
for attr in attrs:
    headers |= json.loads(html.unescape(attr))
response = client.delete(url, headers=headers)
assert response.status_code != 403, "DELETE rejected by CSRF: no token in hx-headers"
assert not Product.objects.filter(pk=product.pk).exists(), response.status_code
print("csrf delete assertion passed")
'
```

## Review

```text
Review the `catalog` app in this Django project (package `my_app`).

Verify these facts:

1. `my_app/catalog/views.py` has list, detail, create, edit and delete views for
   `Product`. Every view has an HTTP method decorator and `@login_required`.
2. The delete view deletes only on a `DELETE` request, never on `GET`.
3. `my_app/catalog/forms.py` defines a `ModelForm` for `Product` with an explicit
   field list (not `"__all__"`).
4. The templates under `templates/catalog/` extend `base.html`, and none renders
   user data with `|safe` or inside `x-data`, `@...` or `hx-on:*` attributes.
5. `my_app/catalog/tests/test_views.py` covers each view, including the
   not-logged-in redirect and a 404 for a missing object.
6. The app's URLs are included from `config/urls.py`.

Context: `HtmxRedirectMiddleware` in `my_app/middleware.py` turns a redirect
returned to an htmx request into an `HX-Location` response, so htmx loads the
target with a GET. Read it before judging redirects after `hx-delete`.
```
