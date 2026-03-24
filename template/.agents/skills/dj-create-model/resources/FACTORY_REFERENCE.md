# factory-boy field reference

Use this table when writing `DjangoModelFactory` classes.

| Django field | factory-boy declaration |
|---|---|
| `CharField` (name-like) | `factory.Faker("name")` |
| `CharField` (generic) | `factory.Faker("word")` |
| `TextField` | `factory.Faker("paragraph")` |
| `EmailField` | `factory.Faker("email")` |
| `URLField` | `factory.Faker("url")` |
| `SlugField` | `factory.Faker("slug")` |
| `IntegerField` | `factory.Faker("random_int")` |
| `BooleanField` | `factory.Faker("boolean")` |
| `DateField` | `factory.Faker("date_object")` |
| `DateTimeField` | `factory.Faker("date_time_this_decade")` |
| `DecimalField` | `factory.Faker("pydecimal", left_digits=4, right_digits=2, positive=True)` |
| `FloatField` | `factory.Faker("pyfloat", positive=True)` |
| `ForeignKey` / `OneToOneField` | `factory.SubFactory(<TargetFactory>)` |
| `ManyToManyField` | `@factory.post_generation` (see below) |
| `FileField` / `ImageField` | omit from factory (leave at field default) |
| field with `choices` | `factory.Iterator([v for v, _ in <Model>.<Choices>.choices])` |

## M2M post_generation pattern

```python
@factory.post_generation
def <field_name>(self, create, extracted, **kwargs):
    if not create or not extracted:
        return
    self.<field_name>.set(extracted)
```

## Notes

- For nullable FK/O2O, still default to a `SubFactory` — tests that need `None` can override.
- Timestamps (`created`, `updated`) with `auto_now_add`/`auto_now` are set by Django automatically — do not declare them in the factory.
