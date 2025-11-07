from datetime import date
from decimal import Decimal

from django.contrib.auth.models import AbstractUser
from django.core.exceptions import ValidationError
from django.core.validators import MinValueValidator, RegexValidator
from django.db import models
from django.utils.translation import gettext_lazy as _


class User(AbstractUser):
    """Custom user that captures the role hierarchy required by the platform."""

    class Roles(models.TextChoices):
        ADMIN = "admin", _("Administrador")
        COMMERCIAL = "commercial", _("Comercial")
        REGISTERED = "registered", _("Usuario registrado")

    role = models.CharField(
        max_length=20,
        choices=Roles.choices,
        default=Roles.REGISTERED,
        help_text=_("Determina los permisos generales del usuario"),
    )

    @property
    def is_commercial(self) -> bool:
        return self.role == self.Roles.COMMERCIAL


class Car(models.Model):
    """Car listing entity published by administrators."""

    MAX_PHOTOS = 10

    license_plate_validator = RegexValidator(
        regex=r"^[A-Z0-9-]{4,10}$",
        message=_("La matrícula solo puede contener letras, números o guiones."),
    )

    license_plate = models.CharField(
        max_length=10,
        unique=True,
        validators=[license_plate_validator],
        verbose_name=_("matrícula"),
    )
    brand = models.CharField(max_length=50, verbose_name=_("marca"))
    model_name = models.CharField(max_length=80, verbose_name=_("modelo"))
    kilometers = models.PositiveIntegerField(
        validators=[MinValueValidator(0)],
        verbose_name=_("kilómetros"),
    )
    year = models.PositiveIntegerField(verbose_name=_("año de fabricación"))
    price = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        validators=[MinValueValidator(Decimal("0.0"))],
        verbose_name=_("precio"),
        default=Decimal("0.00"),
    )
    description = models.TextField(blank=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    created_by = models.ForeignKey(
        "User",
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="cars_created",
    )

    class Meta:
        ordering = ["-created_at"]
        verbose_name = _("anuncio")
        verbose_name_plural = _("anuncios")

    def __str__(self) -> str:
        return f"{self.brand} {self.model_name} - {self.license_plate}"

    def clean(self) -> None:
        """Ensure the year is within a reasonable range."""
        super().clean()
        current_year = date.today().year
        if not 1970 <= self.year <= current_year + 1:
            raise ValidationError(
                {"year": _("El año debe estar entre 1970 y el próximo año.")}
            )

    @property
    def cover_photo(self):
        return self.photos.first()

    def save(self, *args, **kwargs):
        if self.license_plate:
            self.license_plate = self.license_plate.upper()
        self.full_clean()
        super().save(*args, **kwargs)


class CarPhoto(models.Model):
    """Stores the gallery of up to 10 images per car."""

    car = models.ForeignKey(
        Car,
        related_name="photos",
        on_delete=models.CASCADE,
    )
    image = models.ImageField(upload_to="cars/%Y/%m/%d")
    position = models.PositiveSmallIntegerField(default=0)
    uploaded_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["position", "id"]
        verbose_name = _("foto")
        verbose_name_plural = _("fotos")

    def __str__(self) -> str:
        return f"Foto {self.position} de {self.car}"

    def clean(self) -> None:
        """Hard cap of MAX_PHOTOS per listing."""
        super().clean()
        if not self.car_id:
            return

        existing = (
            CarPhoto.objects.filter(car_id=self.car_id)
            .exclude(pk=self.pk)
            .count()
        )
        if existing >= Car.MAX_PHOTOS:
            raise ValidationError(
                _("Cada anuncio puede tener un máximo de 10 fotografías.")
            )

    def save(self, *args, **kwargs):
        self.full_clean()
        super().save(*args, **kwargs)
