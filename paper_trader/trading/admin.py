from django.contrib import admin
from .models import Instrument, Portfolio, Holding, Transaction

admin.site.register(Instrument)
admin.site.register(Portfolio)
admin.site.register(Holding)
admin.site.register(Transaction)