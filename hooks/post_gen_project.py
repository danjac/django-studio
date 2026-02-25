#!/usr/bin/env python
"""Post-generation hook: adjusts files based on cookiecutter choices."""

import os

USE_HX_BOOST = "{{cookiecutter.use_hx_boost}}"

BASE_HTML = os.path.join("templates", "base.html")
DEFAULT_BASE_HTML = os.path.join("templates", "default_base.html")
HX_BASE_HTML = os.path.join("templates", "hx_base.html")


def disable_hx_boost() -> None:
    """Remove hx-boost wiring when the user opts out."""
    # base.html: drop the HTMX/full-page switch, just extend default_base
    with open(BASE_HTML, "w") as f:
        f.write('{% extends "default_base.html" %}\n')

    # default_base.html: remove hx-boost attribute from <body>
    with open(DEFAULT_BASE_HTML) as f:
        content = f.read()
    content = content.replace('\n    hx-boost="true"', "")
    with open(DEFAULT_BASE_HTML, "w") as f:
        f.write(content)

    # hx_base.html is only needed for boosted navigation — remove it
    if os.path.exists(HX_BASE_HTML):
        os.remove(HX_BASE_HTML)


if USE_HX_BOOST == "n":
    disable_hx_boost()
