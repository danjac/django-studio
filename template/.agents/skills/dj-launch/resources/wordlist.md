# Slug word list

Used to generate human-readable random slugs for the Django admin URL.
Pick one adjective and one noun at random: `<adjective>-<noun>/`

## Adjectives

```
amber azure brave calm cold dark deep fast
gold iron jade keen lime mist navy oak pale
pine sage salt sand silk snow soft teal warm
```

## Nouns

```
arch bay cliff cove creek dale dell dune fall
fen ford glen hill isle lake mead moor peak
pool rill rock shore vale weald well wood
```

## Python snippet

```python
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

slug = f"{random.choice(ADJECTIVES)}-{random.choice(NOUNS)}"
```
