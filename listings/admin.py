from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.utils.translation import gettext_lazy as _

from .models import Car, CarPhoto, User


@admin.register(User)
class UserAdmin(BaseUserAdmin):
    """Expose user roles within the Django admin."""

    fieldsets = BaseUserAdmin.fieldsets + (
        (_("Rol"), {"fields": ("role",)}),
    )
    add_fieldsets = BaseUserAdmin.add_fieldsets + (
        (_("Rol"), {"fields": ("role",)}),
    )
    list_display = (*BaseUserAdmin.list_display, "role")
    list_filter = (*BaseUserAdmin.list_filter, "role")


class CarPhotoInline(admin.TabularInline):
    model = CarPhoto
    extra = 1
    max_num = Car.MAX_PHOTOS


@admin.register(Car)
class CarAdmin(admin.ModelAdmin):
    list_display = (
        "license_plate",
        "brand",
        "model_name",
        "kilometers",
        "year",
        "price",
        "is_active",
    )
    list_filter = ("brand", "year", "is_active")
    search_fields = ("license_plate", "brand", "model_name")
    readonly_fields = ("created_at", "updated_at")
    inlines = [CarPhotoInline]

# Register your models here.
