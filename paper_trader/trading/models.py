from django.db import models

class Instrument(models.Model):
    name = models.CharField(max_length=100)
    symbol = models.CharField(max_length=10, unique=True)
    current_price = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)

    def __str__(self):
        return f"{self.name} ({self.symbol})"


class Portfolio(models.Model):
    cash_balance = models.DecimalField(max_digits=12, decimal_places=2, default=10000)  # start with $10,000
    reset_timestamp = models.DateTimeField(auto_now=True)
    def __str__(self):
        return f"Portfolio - Cash: ${self.cash_balance}"


class Holding(models.Model):
    portfolio = models.ForeignKey(Portfolio, on_delete=models.CASCADE, related_name="holdings")
    instrument = models.ForeignKey(Instrument, on_delete=models.CASCADE)
    quantity = models.DecimalField(max_digits=12, decimal_places=4)

    def __str__(self):
        return f"{self.instrument.symbol} - {self.quantity} shares"


class Transaction(models.Model):
    BUY = 'BUY'
    SELL = 'SELL'
    TYPE_CHOICES = [(BUY, 'Buy'), (SELL, 'Sell')]

    portfolio = models.ForeignKey(Portfolio, on_delete=models.CASCADE, related_name="transactions")
    instrument = models.ForeignKey(Instrument, on_delete=models.CASCADE)
    type = models.CharField(max_length=4, choices=TYPE_CHOICES)
    quantity = models.DecimalField(max_digits=12, decimal_places=4)
    price = models.DecimalField(max_digits=12, decimal_places=2)
    timestamp = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.type} {self.quantity} {self.instrument.symbol} @ {self.price}"