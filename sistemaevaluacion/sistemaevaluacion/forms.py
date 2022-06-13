from django import forms

class Scripts(forms.Form):
    desc = forms.CharField(max_length=255)
    entr = forms.CharField(max_length=100)
    sal = forms.CharField(max_length=100)
    scriptT = forms.FileField()
    scriptCEF = forms.FileField()
    scriptCP = forms.FileField()