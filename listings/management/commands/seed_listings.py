import random
from decimal import Decimal
from io import BytesIO

from django.core.files.base import ContentFile
from django.core.management.base import BaseCommand

from PIL import Image, ImageDraw

from listings.models import Car, CarPhoto, User

SAMPLE_CARS = [
    {
        "license_plate": "1234ABC",
        "brand": "Seat",
        "model_name": "Ibiza FR",
        "kilometers": 45000,
        "year": 2019,
        "price": Decimal("13500.00"),
        "description": "Compacto ágil con mantenimiento al día y paquete FR.",
    },
    {
        "license_plate": "5678BCD",
        "brand": "Audi",
        "model_name": "A3 Sportback",
        "kilometers": 52000,
        "year": 2018,
        "price": Decimal("19800.00"),
        "description": "Acabado S-Line, historial completo Audi y un único propietario.",
    },
    {
        "license_plate": "9101CDE",
        "brand": "BMW",
        "model_name": "Serie 1 118d",
        "kilometers": 61000,
        "year": 2020,
        "price": Decimal("22800.00"),
        "description": "Motor eficiente y paquete M interior, listo para viajar.",
    },
    {
        "license_plate": "2345DEF",
        "brand": "Mercedes",
        "model_name": "Clase A 200",
        "kilometers": 28000,
        "year": 2021,
        "price": Decimal("31500.00"),
        "description": "Tecnología MBUX y asistencias completas de conducción.",
    },
    {
        "license_plate": "6789EFG",
        "brand": "Volkswagen",
        "model_name": "Golf GTI",
        "kilometers": 40000,
        "year": 2019,
        "price": Decimal("25500.00"),
        "description": "Edición Performance con llantas 19'' y interior en cuero.",
    },
    {
        "license_plate": "3456FGH",
        "brand": "Tesla",
        "model_name": "Model 3",
        "kilometers": 22000,
        "year": 2022,
        "price": Decimal("38900.00"),
        "description": "Autopilot mejorado y paquete Premium.",
    },
    {
        "license_plate": "7890GHI",
        "brand": "Peugeot",
        "model_name": "3008 GT",
        "kilometers": 50000,
        "year": 2019,
        "price": Decimal("24500.00"),
        "description": "SUV con pack GT Line e interior i-Cockpit panorámico.",
    },
    {
        "license_plate": "4567HIJ",
        "brand": "Renault",
        "model_name": "Clio RS",
        "kilometers": 38000,
        "year": 2018,
        "price": Decimal("16800.00"),
        "description": "Edición limitada Trophy con escape Akrapovič.",
    },
    {
        "license_plate": "8901IJK",
        "brand": "Ford",
        "model_name": "Mustang",
        "kilometers": 32000,
        "year": 2017,
        "price": Decimal("35500.00"),
        "description": "V8 5.0 con paquete Premium y sonido Shaker.",
    },
    {
        "license_plate": "5678JKL",
        "brand": "Kia",
        "model_name": "Sportage",
        "kilometers": 27000,
        "year": 2021,
        "price": Decimal("21500.00"),
        "description": "Garantía oficial vigente y conectividad completa.",
    },
]


def generate_image_bytes(text: str, color: str) -> bytes:
    img = Image.new("RGB", (1200, 800), color)
    draw = ImageDraw.Draw(img)
    draw.text((50, 50), text, fill=(255, 255, 255))
    buffer = BytesIO()
    img.save(buffer, format="JPEG", quality=80)
    return buffer.getvalue()


class Command(BaseCommand):
    help = "Seed the database with 10 car listings and demo images."

    def handle(self, *args, **options):
        admin = (
            User.objects.filter(role=User.Roles.ADMIN).first()
            or User.objects.create_superuser(
                username="admin_seed",
                email="admin_seed@example.com",
                password="admin123",
                role=User.Roles.ADMIN,
            )
        )

        created = 0
        colors = ["#0f172a", "#145388", "#ef4444", "#22c55e", "#f97316"]

        for payload in SAMPLE_CARS:
            car, is_created = Car.objects.get_or_create(
                license_plate=payload["license_plate"],
                defaults={
                    "brand": payload["brand"],
                    "model_name": payload["model_name"],
                    "kilometers": payload["kilometers"],
                    "year": payload["year"],
                    "price": payload["price"],
                    "description": payload["description"],
                    "created_by": admin,
                    "is_active": True,
                },
            )
            if not is_created:
                continue

            self.stdout.write(f"Creado anuncio {car}")
            created += 1

            # attach demo photos
            total_photos = random.randint(2, 4)
            for idx in range(total_photos):
                image_bytes = generate_image_bytes(
                    f"{car.brand} {car.model_name}", random.choice(colors)
                )
                photo = CarPhoto(
                    car=car,
                    position=idx,
                )
                photo.image.save(
                    f"{car.license_plate.lower()}_{idx}.jpg",
                    ContentFile(image_bytes),
                    save=True,
                )

        if created:
            self.stdout.write(
                self.style.SUCCESS(
                    f"Se insertaron {created} anuncios. Admin semilla: {admin.username} / admin123"
                )
            )
        else:
            self.stdout.write(self.style.WARNING("No se crearon anuncios nuevos."))
