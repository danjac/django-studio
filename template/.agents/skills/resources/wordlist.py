# ruff: noqa: INP001
"""Word lists for generating human-readable admin URL slugs.

Usage:
    slug = f"{random.choice(ADJECTIVES)}-{random.choice(NOUNS)}/"
"""

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
