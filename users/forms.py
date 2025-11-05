from django import forms
from .models import item, user, order
class orderform(forms.ModelForm):
    class Meta:
        model = order
        fields = ['address', 'quantity']
