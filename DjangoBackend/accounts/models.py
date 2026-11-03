from django.contrib.auth.models import AbstractUser, BaseUserManager
from django.db import models


class UserManager(BaseUserManager):
    """Tells Django how to create users when login is EMAIL, not username."""

    use_in_migrations = True

    def _create_user(self, email, password, **extra):
        if not email:
            raise ValueError("Email is required")
        email = self.normalize_email(email).lower()
        user = self.model(email=email, **extra)
        user.set_password(password)          # hashes password (PBKDF2)
        user.save(using=self._db)
        return user

    def create_user(self, email, password=None, **extra):
        extra.setdefault("is_staff", False)
        extra.setdefault("is_superuser", False)
        return self._create_user(email, password, **extra)

    def create_superuser(self, email, password=None, **extra):
        extra.setdefault("is_staff", True)
        extra.setdefault("is_superuser", True)
        extra.setdefault("role", "admin")    # also admin in OUR API
        return self._create_user(email, password, **extra)


class User(AbstractUser):
    class Role(models.TextChoices):
        USER = "user", "User"
        ADMIN = "admin", "Admin"

    # Remove fields we don't use
    username = None
    first_name = None
    last_name = None

    # Our fields. password, is_active, date_joined come from AbstractUser
    name = models.CharField(max_length=100)
    email = models.EmailField(unique=True)
    role = models.CharField(max_length=20, choices=Role.choices, default=Role.USER)
    reminders_enabled = models.BooleanField(default=True)
    resume_path = models.CharField(max_length=255, blank=True, null=True)
    resume_text = models.TextField(blank=True, null=True)          # extracted text only
    resume_name = models.CharField(max_length=255, blank=True, null=True)
    resume_updated_at = models.DateTimeField(blank=True, null=True)

    USERNAME_FIELD = "email"       # login with email
    REQUIRED_FIELDS = ["name"]     # asked by createsuperuser

    objects = UserManager()

    def __str__(self):
        return self.email