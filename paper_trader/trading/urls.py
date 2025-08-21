from django.urls import path
from . import views

urlpatterns = [
    path('instrument/<str:symbol>/', views.instrument_detail, name='instrument_detail'),
    path('', views.instrument_list, name='instrument_list'),
]