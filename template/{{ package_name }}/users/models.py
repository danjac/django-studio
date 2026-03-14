from django.contrib.auth.models import AbstractUser


class User(AbstractUser):
    """Custom User model."""

    @property
    def name(self) -> str:
        """Return the user's first name or username."""
        return self.first_name or self.username
