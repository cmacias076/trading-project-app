from django.urls import path
from . import views

urlpatterns = [
    path('', views.instrument_list, name='home'),
    path('instrument/<str:symbol>/', views.instrument_detail, name='instrument_detail'),
    path('instruments/', views.instrument_list, name='instrument_list'),
    path('portfolio/', views.portfolio_view, name='portfolio'),
    path('reset/', views.reset_portfolio, name='reset_portfolio'),
]
