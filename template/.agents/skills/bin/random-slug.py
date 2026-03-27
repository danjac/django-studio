#!/usr/bin/env -S uv run python
# ruff: noqa: INP001, T201, S311
"""Print a random human-readable slug in the form <adjective>-<noun>.

Usage:
    .agents/skills/bin/random-slug.py
    # → calm-peak
"""

import random

ADJECTIVES = [
    "amber", "azure", "brave", "calm", "cold", "dark", "deep", "fast",
    "gold", "iron", "jade", "keen", "lime", "mist", "navy", "oak", "pale",
    "pine", "sage", "salt", "sand", "silk", "snow", "soft", "teal", "warm",
]

NOUNS = [
    "arch", "bay", "cliff", "cove", "creek", "dale", "dell", "dune", "fall",
    "fen", "ford", "glen", "hill", "isle", "lake", "mead", "moor", "peak",
    "pool", "rill", "rock", "shore", "vale", "weald", "well", "wood",
]

if __name__ == "__main__":
    print(f"{random.choice(ADJECTIVES)}-{random.choice(NOUNS)}")
