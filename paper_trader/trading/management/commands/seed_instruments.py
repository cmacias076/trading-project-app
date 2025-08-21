from django.core.management.base import BaseCommand
from trading.models import Instrument

class Command(BaseCommand):
    help = "Seed the database with some default financial instruments"

    def handle(self, *args, **kwargs):
        instruments = [
            {"name": "Apple", "symbol": "AAPL"},
            {"name": "Tesla", "symbol": "TSLA"},
            {"name": "Microsoft", "symbol": "MSFT"},
        ]

        for inst in instruments:
            obj, created = Instrument.objects.get_or_create(
                symbol=inst["symbol"],
                defaults={"name": inst["name"], "current_price": 0.00}
            )
            if created:
                self.stdout.write(self.style.SUCCESS(f"Added {inst['name']} ({inst['symbol']})"))
            else:
                self.stdout.write(self.style.WARNING(f"{inst['symbol']} already exists"))