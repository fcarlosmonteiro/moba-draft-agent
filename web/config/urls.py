from django.urls import include, path

from chat import views

urlpatterns = [
    path("login/", views.login_view, name="login"),
    path("logout/", views.logout_view, name="logout"),
    path("", include("chat.urls")),
]
