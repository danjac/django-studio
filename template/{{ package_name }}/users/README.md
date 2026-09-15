# Users

User accounts and account deletion. Sign-up, login, email verification and social
accounts are handled by allauth (see `docs/authentication.md`); this app owns the
custom `User` model and the right-to-erasure flow.

> Starting point shipped by the template. Extend it as you customise the `User`
> model — run `/dj-doc users` to update it.

## Concepts

- **User** — _TODO: what a user represents in this project (an individual, a member
  of an organisation, a customer)._
- **Anonymised user** — a deleted account. The row is kept so foreign keys stay
  valid, but all personal data is overwritten and the account can never log in again.

## Business rules

| Rule | Why | Enforced in |
| ---- | --- | ----------- |
| Deleting an account anonymises the user instead of deleting the row | Keeps related records intact while meeting GDPR Article 17 | `users/gdpr.py::anonymise_user` |
| An anonymised user cannot log in | Erasure must be irreversible | `users/gdpr.py::anonymise_user` (inactive, unusable password, allauth records removed) |
| Only the signed-in user can delete their own account | Self-service erasure | `users/views.py::delete_account_confirm` (`login_required`, acts on `request.user`) |

## Lifecycle

```
active ──delete account──▶ anonymised
```

- **active** — a normal account.
- **anonymised** — username `deleted-<pk>`, email `deleted-<pk>@example.invalid`,
  names blank, `is_active=False`, no email addresses or social accounts.

## Personal data

- `User`: `username`, `email`, `first_name`, `last_name`.
- allauth: `EmailAddress`, `SocialAccount`.

Erasure: `users/gdpr.py::anonymise_user`. Other apps that store personal data linked
to a user must clean it up by connecting to the `pre_anonymise_user` signal (original
data still readable) or `post_anonymise_user`. See `docs/gdpr.md`.

## Gotchas and decisions

- The `User` model ships without an initial migration so fields can be customised
  before the first `makemigrations`.
- `User.name` falls back to `username` when `first_name` is blank.

## Reference

- Models: `users/models.py` — `User`
- Erasure: `users/gdpr.py` — `anonymise_user`
- Signals: `users/signals.py` — `pre_anonymise_user`, `post_anonymise_user`
- URLs: `users` namespace in `users/urls.py` — `delete_account`, `delete_account_confirm`
- Admin: `users/admin.py` — `UserAdmin`
- Depends on: allauth
