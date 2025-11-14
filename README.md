# Compramos Tu Coche

Aplicación web en Django 5.2 que permite publicar y explorar anuncios de coches de segunda mano. Incluye una jerarquía de roles (administrador, comercial, usuario registrado y anónimo), catálogo público filtrable y backend de administración para gestionar anuncios y galerías de fotos.

## Requisitos

- Python 3.10+
- `virtualenv` o `venv`
- Dependencias listadas en `requirements.txt`

## Puesta en marcha

1. **Clonar y crear entorno virtual**
   ```bash
   python3 -m venv venv
   source venv/bin/activate
   ```

2. **Instalar dependencias**
   ```bash
   pip install -r requirements.txt
   ```

3. **Aplicar migraciones**
   ```bash
   python manage.py migrate
   ```

4. **Crear superusuario**
   ```bash
   python manage.py createsuperuser
   ```
   El superusuario actúa como administrador y podrá subir anuncios desde `/admin/`.

5. **Ejecutar servidor de desarrollo**
   ```bash
   python manage.py runserver
   ```
   Visita `http://127.0.0.1:8000/` para el catálogo público y `http://127.0.0.1:8000/admin/` para el panel de administración.

## Gestión de anuncios

- Los administradores crean anuncios (`Car`) y suben hasta 10 fotos (`CarPhoto`) por vehículo.
- Los anuncios contienen: matrícula, marca, modelo, kilómetros, año, descripción opcional y galerías.
- Desde la página principal los usuarios (anónimos o registrados) pueden filtrar por marca, modelo, rango de años, kilometraje máximo o texto libre (marca/modelo/matrícula).

## Pruebas automatizadas

Ejecuta la suite de tests para validar filtros y reglas de negocio:
```bash
python manage.py test
```

## Archivos estáticos y media

- Archivos estáticos gestionados con Tailwind vía CDN (ver `templates/base.html`).
- Ficheros subidos (fotos): `media/`
- Durante desarrollo, Django sirve ambos automáticamente con `DEBUG=True`. En producción deberás configurar un servidor para `MEDIA_URL` y `STATIC_URL`.

## Roles y autenticación

- `Administrador`: gestiona usuarios y anuncios desde el admin.
- `Comercial`: preparado para futuras vistas con permisos de edición limitados.
- `Usuario registrado`: puede autenticarse para futuras funcionalidades.
- `Anónimo`: acceso de solo lectura al listado público.

Ajusta permisos o vistas adicionales en `listings/models.py` y `listings/views.py` según tus necesidades.

## Compra y Stripe

Los usuarios anónimos pueden explorar el catálogo, pero al pulsar **Comprar** se les redirige al login/registro. El flujo de compra crea una sesión de Stripe Checkout con el precio indicado en cada anuncio.

Configura tus credenciales en variables de entorno antes de arrancar:
```bash
export STRIPE_SECRET_KEY=sk_test_xxx
export STRIPE_PUBLISHABLE_KEY=pk_test_xxx
export STRIPE_SUCCESS_URL="http://127.0.0.1:8000/?pago=exitoso"
export STRIPE_CANCEL_URL="http://127.0.0.1:8000/?pago=cancelado"
```

## Datos de ejemplo

Hay un comando para sembrar 10 anuncios con fotos generadas dinámicamente:
```bash
python manage.py seed_listings
```

El comando también crea (si no existe) el superusuario `admin_seed / admin123`.

Para adjuntar fotos reales desde Internet (Pexels en este ejemplo) ejecuta, con conexión activa:
```bash
python manage.py fetch_demo_photos
```
Usa `--force` si quieres reemplazar las fotos existentes. Revisa/edita las URLs en `listings/management/commands/fetch_demo_photos.py` para apuntar a tus propias imágenes y asegúrate de respetar las licencias.

# Anem a usar un model de predicció de preu 
https://github.com/dianisay/Machine-Learning-for-Used-Car-Price-Prediction.git