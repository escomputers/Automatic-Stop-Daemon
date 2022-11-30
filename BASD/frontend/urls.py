from django.urls import path
from django.views.generic import TemplateView
from django.conf import settings
from django.conf.urls.static import static

from . import views

urlpatterns = [
    path('', TemplateView.as_view(template_name='index.html'), name="index"),
    path("getData/", views.getData, name="getData"),
    # path("success/", views.success, name="success"),
    path('success/', TemplateView.as_view(template_name='success.html'), name="success")
]
