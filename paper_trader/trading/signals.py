from django.db.models.signals import post_migrate
from django.dispatch import receiver
from .models import Portfolio

@receiver(post_migrate)
def create_default_portfolio(sender, **kwargs):
    if sender.name == "trading": 
          if not Portfolio.objects.exists():
            Portfolio.objects.create(cash_balance=10000)