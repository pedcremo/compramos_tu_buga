import itertools

import requests
from django.core.files.base import ContentFile
from django.core.management.base import BaseCommand

from listings.models import Car, CarPhoto

# Pexels URLs (licencia gratuita). Sustituye por tus propias fuentes si lo prefieres.
EXTERNAL_SOURCES = {
    "1234ABC": [
        "https://images.pexels.com/photos/210019/pexels-photo-210019.jpeg",
        "https://images.pexels.com/photos/170811/pexels-photo-170811.jpeg",
        "https://images.pexels.com/photos/120049/pexels-photo-120049.jpeg",
    ],
    "5678BCD": [
        "https://images.pexels.com/photos/1402787/pexels-photo-1402787.jpeg",
        "https://images.pexels.com/photos/1402785/pexels-photo-1402785.jpeg",
        "https://images.pexels.com/photos/2100190/pexels-photo-2100190.jpeg",
    ],
    "9101CDE": [
        "https://images.pexels.com/photos/358070/pexels-photo-358070.jpeg",
        "https://images.pexels.com/photos/2100191/pexels-photo-2100191.jpeg",
        "https://images.pexels.com/photos/1708119/pexels-photo-1708119.jpeg",
    ],
    "2345DEF": [
        "https://images.pexels.com/photos/575821/pexels-photo-575821.jpeg",
        "https://images.pexels.com/photos/1149831/pexels-photo-1149831.jpeg",
        "https://images.pexels.com/photos/1149833/pexels-photo-1149833.jpeg",
    ],
    "6789EFG": [
        "https://images.pexels.com/photos/1545743/pexels-photo-1545743.jpeg",
        "https://images.pexels.com/photos/2100193/pexels-photo-2100193.jpeg",
        "https://images.pexels.com/photos/1200491/pexels-photo-1200491.jpeg",
    ],
    "3456FGH": [
        "https://images.pexels.com/photos/799443/pexels-photo-799443.jpeg",
        "https://images.pexels.com/photos/123335/pexels-photo-123335.jpeg",
        "https://images.pexels.com/photos/112460/pexels-photo-112460.jpeg",
    ],
    "7890GHI": [
        "https://images.pexels.com/photos/2100194/pexels-photo-2100194.jpeg",
        "https://images.pexels.com/photos/2100195/pexels-photo-2100195.jpeg",
        "https://images.pexels.com/photos/376498/pexels-photo-376498.jpeg",
    ],
    "4567HIJ": [
        "https://images.pexels.com/photos/2100196/pexels-photo-2100196.jpeg",
        "https://images.pexels.com/photos/266621/pexels-photo-266621.jpeg",
        "https://images.pexels.com/photos/386009/pexels-photo-386009.jpeg",
    ],
    "8901IJK": [
        "https://images.pexels.com/photos/2100197/pexels-photo-2100197.jpeg",
        "https://images.pexels.com/photos/2100198/pexels-photo-2100198.jpeg",
        "https://images.pexels.com/photos/1805053/pexels-photo-1805053.jpeg",
    ],
    "5678JKL": [
        "https://images.pexels.com/photos/2100199/pexels-photo-2100199.jpeg",
        "https://images.pexels.com/photos/1149834/pexels-photo-1149834.jpeg",
        "https://images.pexels.com/photos/1149058/pexels-photo-1149058.jpeg",
    ],
}


class Command(BaseCommand):
    help = "Descarga fotos libres de Pexels/URLs configuradas y las asigna a cada anuncio."

    def add_arguments(self, parser):
        parser.add_argument(
            "--force",
            action="store_true",
            help="Reemplaza todas las fotos existentes por las descargadas.",
        )

    def handle(self, *args, **options):
        force = options["force"]
        total_downloaded = 0

        for license_plate, urls in EXTERNAL_SOURCES.items():
            car = Car.objects.filter(license_plate=license_plate).first()
            if not car:
                self.stdout.write(self.style.WARNING(f"No existe {license_plate}, se omite."))
                continue

            if not force:
                existing = car.photos.count()
                if existing >= len(urls):
                    self.stdout.write(
                        self.style.NOTICE(
                            f"{car} ya tiene {existing} fotos, usa --force para reemplazar."
                        )
                    )
                    continue
            else:
                car.photos.all().delete()

            for position, url in enumerate(urls):
                try:
                    self.stdout.write(f"Descargando {url} para {car}...")
                    response = requests.get(url, timeout=30)
                    response.raise_for_status()
                except requests.RequestException as exc:
                    self.stdout.write(self.style.ERROR(f"Error descargando {url}: {exc}"))
                    continue

                filename = f"{license_plate.lower()}_{position}.jpg"
                photo = CarPhoto(car=car, position=position)
                photo.image.save(filename, ContentFile(response.content), save=True)
                total_downloaded += 1

        self.stdout.write(self.style.SUCCESS(f"Fotos descargadas: {total_downloaded}"))
