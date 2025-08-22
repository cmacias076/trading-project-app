from django import forms

class BuyForm(forms.Form):
    quantity = forms.DecimalField(
        min_value=0.0001, 
        decimal_places=4, 
        label='Quantity to Buy'
    )