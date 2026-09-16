from django import forms

from .models import ContentBlock, FAQ, LegalPage, PageSEO, SiteSettings


class StyledModelForm(forms.ModelForm):
    """Same `.field` auto-styling as properties.forms.StyledModelForm."""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        skip = (forms.CheckboxInput, forms.CheckboxSelectMultiple, forms.RadioSelect)
        for field in self.fields.values():
            if isinstance(field.widget, skip):
                continue
            existing = field.widget.attrs.get('class', '')
            field.widget.attrs['class'] = f'{existing} field'.strip()


class FAQForm(StyledModelForm):
    class Meta:
        model = FAQ
        fields = ['question', 'answer', 'placement', 'order', 'is_published']
        widgets = {
            'answer': forms.Textarea(attrs={'rows': 4, 'maxlength': 1000}),
        }


class SiteSettingsForm(StyledModelForm):
    class Meta:
        model = SiteSettings
        fields = [
            'platform_name', 'logo', 'favicon',
            'support_phone', 'support_email', 'business_address',
            'facebook_url', 'instagram_url', 'twitter_url', 'linkedin_url',
        ]


class PropertyLimitsForm(StyledModelForm):
    class Meta:
        model = SiteSettings
        fields = ['max_photos_per_listing', 'min_photos_to_publish']


class SeoSettingsForm(StyledModelForm):
    class Meta:
        model = SiteSettings
        fields = ['google_analytics_id', 'facebook_pixel_id', 'og_image']


class PageSEOForm(StyledModelForm):
    class Meta:
        model = PageSEO
        fields = ['meta_title', 'meta_description']
        widgets = {'meta_description': forms.Textarea(attrs={'rows': 3, 'maxlength': 160})}


class LegalPageForm(StyledModelForm):
    class Meta:
        model = LegalPage
        fields = ['title', 'body']
        widgets = {'body': forms.Textarea(attrs={'rows': 18})}


class ContentBlockForm(StyledModelForm):
    class Meta:
        model = ContentBlock
        fields = ['placement', 'icon', 'title', 'text', 'order', 'is_published']
