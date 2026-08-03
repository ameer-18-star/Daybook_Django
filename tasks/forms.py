from django import forms
from django.contrib.auth import get_user_model
from django.contrib.auth.forms import UserCreationForm

from .models import TaskTemplate

User = get_user_model()


class RegisterForm(UserCreationForm):
    email = forms.EmailField(required=False)

    class Meta:
        model = User
        fields = ('username', 'email', 'password1', 'password2')

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in self.fields.values():
            field.widget.attrs.setdefault('class', 'task-text-input')


class TaskTemplateForm(forms.ModelForm):
    class Meta:
        model = TaskTemplate
        fields = ['text', 'category', 'priority', 'recurrence_type', 'days_of_week', 'active']
        widgets = {
            'text': forms.TextInput(attrs={'class': 'task-text-input', 'maxlength': 140}),
            'category': forms.Select(attrs={'class': 'select'}),
            'priority': forms.Select(attrs={'class': 'select'}),
            'recurrence_type': forms.Select(attrs={'class': 'select'}),
            'days_of_week': forms.TextInput(attrs={'class': 'task-text-input', 'placeholder': 'e.g. 0,2,4'}),
        }


class CustomReportForm(forms.Form):
    start = forms.DateField(widget=forms.DateInput(attrs={'type': 'date', 'class': 'select'}))
    end = forms.DateField(widget=forms.DateInput(attrs={'type': 'date', 'class': 'select'}))

    def clean(self):
        cleaned = super().clean()
        start, end = cleaned.get('start'), cleaned.get('end')
        if start and end and start > end:
            raise forms.ValidationError('Start date must be before end date.')
        if start and end and (end - start).days > 366:
            raise forms.ValidationError('Range too large — please pick up to one year.')
        return cleaned
