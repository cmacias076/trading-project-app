from django.db import models

class Instrument(models.Model):
    symbol = models.CharField(max_length=10, unique=True)
    name = models.CharField(max_length=100)

    def __str__(self):
        return f"{self.symbol} - {self.name}"

class Portfolio(models.Model):
    cash_balance = models.DecimalField(max_digits=12, decimal_places=2)

    def __str__(self):
        return f"Portfolio - Cash: ${self.cash_balnce}"
    
class Holding(models.Model):
    instrument = models.ForeignKey(Instrument, on_delete=models.CASCADE)
    quantity = models.DecimalField(max_digits=12, decimal_places=4)

    def __str__(self):
        return f"{self.instrument.symbol} - {self.quantity} shares"
    
class Transaction(models.Model):
    BUY = 'BUY'
    SELL = 'SELL'
    TYPE_CHOICES = [(BUY, 'Buy'), (SELL, 'Sell')]

    instrument = models.ForeignKey(Instrument, on_delete=models.CASCADE)
    type = models.CharField(max_length=4, choices=TYPE_CHOICES)
    quantity = models.DecimalField(max_digits=12, decimal_places=4)
    price = models.DecimalField(max_digits=12, decimal_places=2)
    timestamp = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.type} {self.quantity} {self.instrument.symbol} @ {self.price}"

