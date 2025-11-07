from django.conf import settings
from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin
from django.db.models import Q
from django.http import JsonResponse
from django.shortcuts import get_object_or_404
from django.urls import reverse_lazy
from django.views.generic import CreateView, ListView, TemplateView, View

import stripe

from .forms import SignUpForm
from .models import Car


class CarListView(ListView):
    """Public landing page that lists all available cars with filters."""

    template_name = "listings/home.html"
    model = Car
    context_object_name = "cars"
    paginate_by = 12

    def get_queryset(self):
        queryset = (
            Car.objects.filter(is_active=True)
            .prefetch_related("photos")
            .order_by("-created_at")
        )

        brand = self.request.GET.get("brand")
        model_name = self.request.GET.get("model")
        year_min = self.request.GET.get("year_min")
        year_max = self.request.GET.get("year_max")
        km_max = self.request.GET.get("km_max")
        search = self.request.GET.get("q")

        if brand:
            queryset = queryset.filter(brand__iexact=brand)
        if model_name:
            queryset = queryset.filter(model_name__icontains=model_name)
        if year_min:
            try:
                queryset = queryset.filter(year__gte=int(year_min))
            except ValueError:
                pass
        if year_max:
            try:
                queryset = queryset.filter(year__lte=int(year_max))
            except ValueError:
                pass
        if km_max:
            try:
                queryset = queryset.filter(kilometers__lte=int(km_max))
            except ValueError:
                pass
        if search:
            queryset = queryset.filter(
                Q(brand__icontains=search)
                | Q(model_name__icontains=search)
                | Q(license_plate__icontains=search)
            )

        return queryset

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["filter_values"] = {
            "brand": self.request.GET.get("brand", ""),
            "model": self.request.GET.get("model", ""),
            "year_min": self.request.GET.get("year_min", ""),
            "year_max": self.request.GET.get("year_max", ""),
            "km_max": self.request.GET.get("km_max", ""),
            "q": self.request.GET.get("q", ""),
        }
        context["available_brands"] = (
            Car.objects.filter(is_active=True)
            .values_list("brand", flat=True)
            .distinct()
            .order_by("brand")
        )
        context["available_years"] = (
            Car.objects.filter(is_active=True)
            .order_by("year")
            .values_list("year", flat=True)
            .distinct()
        )
        query_params = self.request.GET.copy()
        query_params.pop("page", None)
        context["filters_query"] = query_params.urlencode()
        return context


class SignUpView(CreateView):
    """Simple registration flow so anonymous users can comprar un vehículo."""

    template_name = "registration/signup.html"
    form_class = SignUpForm
    success_url = reverse_lazy("login")

    def form_valid(self, form):
        messages.success(
            self.request,
            "Cuenta creada correctamente. Inicia sesión para continuar con tu compra.",
        )
        return super().form_valid(form)


class CarBuyView(LoginRequiredMixin, TemplateView):
    template_name = "listings/buy.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        car = get_object_or_404(Car, pk=self.kwargs["pk"], is_active=True)
        context["car"] = car
        context["stripe_public_key"] = settings.STRIPE_PUBLISHABLE_KEY
        return context


class CheckoutSessionView(LoginRequiredMixin, View):
    http_method_names = ["post"]

    def post(self, request, pk):
        if not settings.STRIPE_SECRET_KEY or not settings.STRIPE_PUBLISHABLE_KEY:
            return JsonResponse(
                {"error": "Stripe no está configurado. Contacta con el administrador."},
                status=500,
            )

        car = get_object_or_404(Car, pk=pk, is_active=True)
        if car.price <= 0:
            return JsonResponse(
                {"error": "El anuncio no tiene un precio válido."}, status=400
            )

        stripe.api_key = settings.STRIPE_SECRET_KEY
        amount_cents = int(car.price * 100)
        try:
            checkout_kwargs = {
                "mode": "payment",
                "line_items": [
                    {
                        "price_data": {
                            "currency": "eur",
                            "product_data": {
                                "name": f"{car.brand} {car.model_name}",
                                "metadata": {"car_id": car.pk},
                            },
                            "unit_amount": amount_cents,
                        },
                        "quantity": 1,
                    }
                ],
                "success_url": settings.STRIPE_SUCCESS_URL,
                "cancel_url": settings.STRIPE_CANCEL_URL,
                "payment_method_types": ["card"],
                "metadata": {"car_id": car.pk, "user_id": request.user.pk},
            }
            if request.user.email:
                checkout_kwargs["customer_email"] = request.user.email

            session = stripe.checkout.Session.create(**checkout_kwargs)
        except stripe.error.StripeError as exc:
            return JsonResponse(
                {"error": f"Error creando la sesión de pago: {exc.user_message}"},
                status=400,
            )

        return JsonResponse({"sessionId": session.id})
