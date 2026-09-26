**/dj-bootstrap [description]**

Start a new django-studio project without running Copier yourself. The skill
checks your tools, asks for the Copier answers and a few questions about the
product, runs `copier copy`, smoke-tests the result with `just check-all`, and
makes the first commit.

Arguments:
  description   Optional free-text description of the project. Anything it
                states (name, purpose, domain, licence, roles, languages) is
                not asked again.

Run it in an empty directory to generate the project there; in any other
directory it generates into `./<project_slug>`. Requires `uv`, `just`, `docker`
and `gh`.

The generated project is the same as `uvx copier copy` with the same answers, so
`copier update` and `/dj-sync` work on it. The product answers are saved to
`.django_studio/brief.md` in the new project.

Example:
  /dj-bootstrap "recipe sharing site for home cooks"
