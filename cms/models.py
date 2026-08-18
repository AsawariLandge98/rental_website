from django.db import models


class FAQ(models.Model):
    class Placement(models.TextChoices):
        CONTACT = 'contact', 'Contact Page'
        TENANT_HELP = 'tenant_help', 'Tenant Help & Support'

    question = models.CharField(max_length=200)
    answer = models.TextField()
    placement = models.CharField(max_length=20, choices=Placement.choices, default=Placement.CONTACT)
    order = models.PositiveIntegerField(default=0)
    is_published = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'FAQ'
        verbose_name_plural = 'FAQs'
        ordering = ['placement', 'order', 'id']

    def __str__(self):
        return self.question
