from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import Group, User

from .validators import sanitize_input


class RegistroForm(UserCreationForm):
    first_name = forms.CharField(max_length=60, label="Nombres")
    last_name = forms.CharField(max_length=60, label="Apellidos")
    email = forms.EmailField(label="Correo institucional")

    class Meta:
        model = User
        fields = ["username", "first_name", "last_name", "email"]

    def clean_email(self):
        email = sanitize_input(self.cleaned_data["email"]).lower()
        if User.objects.filter(email__iexact=email).exists():
            raise forms.ValidationError("Ya existe una cuenta con este correo.")
        return email

    def clean_first_name(self):
        return sanitize_input(self.cleaned_data["first_name"]).title()

    def clean_last_name(self):
        return sanitize_input(self.cleaned_data["last_name"]).title()

    def save(self, commit=True):
        user = super().save(commit=commit)
        if commit:
            # Todo usuario nuevo entra con el rol de menor privilegio.
            grupo, _ = Group.objects.get_or_create(name="Almacenero")
            user.groups.add(grupo)
        return user