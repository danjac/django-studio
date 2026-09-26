**/djs-kickoff**

Gives a new django-studio project its first shape from the product overview in
`docs/this-project.md`. If the page is still the template stub, it asks the
product questions and writes it first.

Runs these steps, each of which you can skip:

1. User model: proposes `User` fields the overview calls for (usually none).
2. Domain apps and models: proposes an app and model breakdown from the core
   entities, and which models get CRUD views. Nothing is generated until you
   confirm it.
3. Languages: sets up each UI language other than English, and is skipped for
   an English-only site. Needs `gettext`, and asks you to install it if it is
   missing. Translation needs a TranslateBot key; without one, run
   `/djs-localize <locale>` later.
4. Project docs: runs `/djs-doc` to fill in the app map and app READMEs.
5. Optional features: points to the docs for a planned API, webhooks or
   background tasks. It doesn't build them.

Each step follows the project's own `/djs-*` skill. The skill runs
`just check-all` and commits when it passes.

Run it in any new django-studio project. It first runs whatever setup hasn't run
yet: `just install`, a first commit of the scaffold, and the `users` migration.
`/djs-bootstrap` also offers to run it at the end.

Example:
  /djs-kickoff
