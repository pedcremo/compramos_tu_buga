from django.urls import path

from .views import (
    CarBuyView,
    CarListView,
    CheckoutSessionView,
    SignUpView,
)

app_name = "listings"

urlpatterns = [
    path("", CarListView.as_view(), name="home"),
    path("registro/", SignUpView.as_view(), name="signup"),
    path("anuncios/<int:pk>/comprar/", CarBuyView.as_view(), name="car_buy"),
    path(
        "anuncios/<int:pk>/checkout-session/",
        CheckoutSessionView.as_view(),
        name="checkout_session",
    ),
]
