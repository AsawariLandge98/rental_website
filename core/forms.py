from django import forms

from .models import City, ContactMessage, NewsletterSubscriber


class StyledModelForm(forms.ModelForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in self.fields.values():
            existing = field.widget.attrs.get('class', '')
            field.widget.attrs['class'] = f'{existing} field'.strip()


class NewsletterForm(StyledModelForm):
    class Meta:
        model = NewsletterSubscriber
        fields = ['email']
        widgets = {
            'email': forms.EmailInput(attrs={'placeholder': 'Enter your email address'}),
        }

    def clean_email(self):
        email = self.cleaned_data['email'].lower().strip()
        if NewsletterSubscriber.objects.filter(email__iexact=email).exists():
            raise forms.ValidationError("You're already subscribed!")
        return email


class ContactForm(StyledModelForm):
    class Meta:
        model = ContactMessage
        fields = ['name', 'email', 'phone', 'subject', 'message']
        widgets = {
            'name': forms.TextInput(attrs={'placeholder': 'Full Name'}),
            'email': forms.EmailInput(attrs={'placeholder': 'Email Address'}),
            'phone': forms.TextInput(attrs={'placeholder': 'Mobile Number'}),
            'subject': forms.TextInput(attrs={'placeholder': 'Subject'}),
            'message': forms.Textarea(attrs={'placeholder': 'Your Message', 'rows': 6, 'class': 'contact-form__message'}),
        }


class CityForm(StyledModelForm):
    class Meta:
        model = City
        fields = ['name', 'order', 'is_active']

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # StyledModelForm applies `.field` (a full-width bordered text-input
        # style) to every widget, including checkboxes — fine for
        # name/order, but it would badly distort the is_active checkbox.
        self.fields['is_active'].widget.attrs.pop('class', None)
