# Bootstrap a new project

Covers the plugin's `/dj-bootstrap`: preflight, Copier answers taken from the prompt
and the answers below, the product brief, `copier copy`, the smoke test and the
first commit. The runner starts it in an empty directory with the plugin loaded,
and `{template}` is replaced with this checkout, so the case tests the local
template rather than GitHub `main`.

## Prompt

```text
/dj-bootstrap "Recipe Box: a recipe sharing site for home cooks"

Template source: {template}

Copier answers:

- Project name: Recipe Box. Slug: `recipe_box`.
- Description: A recipe sharing site for home cooks
- Author: Eval Author, eval@example.com
- Domain: recipebox.example.com
- License: EUPL-1.2
- Confirm the summary as shown.

Product answers:

- Core entities: Recipe (created by a cook), Ingredient (belongs to a recipe),
  Collection (a cook's named list of recipes).
- User roles: visitors browse and search recipes; cooks (signed-in users) also
  create and edit their own recipes and collections; staff moderate everything.
- Access: public site; login is needed only to post or save recipes.
- Languages: English (default) and French.
- Public API: no. Incoming webhooks: no.
- Background tasks: yes, a weekly digest email of new recipes.

Create a GitHub repository: no.
```

## Check

```sh
grep -qx "project_name: Recipe Box" .copier-answers.yml
grep -qx "project_slug: recipe_box" .copier-answers.yml
grep -qx "package_name: recipe_box" .copier-answers.yml
grep -qx "description: A recipe sharing site for home cooks" .copier-answers.yml
grep -qx "author: Eval Author" .copier-answers.yml
grep -qx "author_email: eval@example.com" .copier-answers.yml
grep -qx "domain: recipebox.example.com" .copier-answers.yml
grep -qx "license: EUPL-1.2" .copier-answers.yml
test -d recipe_box
test -f .django_studio/brief.md
git check-ignore -q .django_studio/brief.md
test -n "$(ls recipe_box/users/migrations/0001_*.py)"
test "$(git rev-list --count HEAD)" = 1
test -z "$(git status --porcelain)"
git ls-files --error-unmatch recipe_box/users/migrations/0001_initial.py
just dj makemigrations --check --dry-run
just check-all
```

## Review

```text
Review the project brief written by a project bootstrap run in this directory.

Verify these facts:

1. `.django_studio/brief.md` has the sections Purpose, Core entities, User roles,
   Access, Languages, Integrations and Other notes.
2. Core entities lists Recipe, Ingredient and Collection.
3. User roles lists visitors, cooks and staff, with what each can do.
4. Access says the site is public and login is needed only to post or save
   recipes.
5. Languages lists English as the default and French.
6. Integrations says no public API, no incoming webhooks, and a background task
   for a weekly digest email.
```
