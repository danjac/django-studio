This is a cookiecutter project to create a new Django project.

## Testing

Create a new project in `/tmp` using the cookiecutter template:

```bash
uvx cookiecutter --no-input --output-dir /tmp ./
```

If a project has already been created in `/tmp`, you can remove it before creating a new one:

```bashbash
cd /tm/my_django_project
just stop # stop the development services if they are running
cd ..
rm -rf my_django_project
```

This will create a new Django project in `/tmp` with the default settings. You can then navigate to the project directory and check if the project was created successfully.

You can test the project by running the following command in the project directory:

```bash
just start # start the development services
just install # install dependencies*
just precommitall # run pre-commit on all files
just lint # run linters
just typecheck # run type checks
just test # run tests
just stop # stop the development services
```

- **Note** you may need to run `uv sync` first to install the dependencies in the virtual environment before running `just install`.

## Cookiecutter Project Testing

The cookiecutter project itself has its own tests and pre-commit config. Run these from the root directory:

```bash
just check      # Run lint, format, and tests
just test      # Run pytest
just lint      # Run ruff on tests
just format    # Check formatting
```

To install pre-commit hooks for the cookiecutter project itself:

```bash
uv run pre-commit install
```

## Design System

The template includes a component library in `{{cookiecutter.project_slug}}/design/`. When modifying or adding UI components in the generated project, check the design system first:

## Design System

The template includes a component library in `{{cookiecutter.project_slug}}/design/`. When modifying or adding UI components in the generated project, check the design system first:

- `design/README.md` — component index and design tokens
- `design/navigation.md` — navbar, sidebar, user dropdown
- `design/forms.md` — form wrapper, field template, input classes
- `design/buttons.md` — button variants
- `design/messages.md` — toast alerts
- `design/cards.md` — link card component
- `design/pagination.md` — paginated list
- `design/typography.md` — markdown/prose, heading scale
- `design/layout.md` — base templates, page layout patterns

Components are sourced from the `radiofeed-app` production codebase and generalized for reuse. When adding a component to the template, add a corresponding doc to `design/`.

## Bugs

User will keep track of bugs in document BUGS.md. Check this and fix them first before adding new features. If you find a bug, please report it in the BUGS.md file with a clear description and steps to reproduce it.
