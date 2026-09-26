# Bootstrap a new project

Covers the plugin's `/djs-bootstrap`: preflight, Copier answers taken from the prompt
and the answers below, `copier copy`, the product overview in
`docs/this-project.md`, the smoke test and the first commit. The runner starts it in an empty directory with the plugin loaded,
and `{template}` is replaced with this checkout, so the case tests the local
template rather than GitHub `main`.

## Prompt

```text
/djs-bootstrap "Recipe Box: a recipe sharing site for home cooks"

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

Kick off the project now: no.
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
git ls-files --error-unmatch docs/this-project.md
! grep -q "djs-doc: stub" docs/this-project.md
test -n "$(ls recipe_box/users/migrations/0001_*.py)"
test "$(git rev-list --count HEAD)" = 1
test -z "$(git status --porcelain)"
git ls-files --error-unmatch recipe_box/users/migrations/0001_initial.py
just dj makemigrations --check --dry-run
just check-all
```

## Review

```text
Review the project overview written by a project bootstrap run in this directory.

Verify these facts about `docs/this-project.md`:

1. It keeps the headings Purpose, Users and Roles, Glossary, Apps, Key Flows,
   Integrations and Key Decisions, and has no "Stub." note.
2. Purpose describes a recipe sharing site for home cooks.
3. Users and Roles has rows for visitors, cooks and staff, with what each can do.
4. Glossary has entries for Recipe, Ingredient and Collection.
5. Key Decisions records: a public site where login is needed only to post or
   save recipes; English (default) and French; no public API; no incoming
   webhooks; and a planned background task for a weekly digest email.
6. Key Flows has a `_TODO` marker.
```
