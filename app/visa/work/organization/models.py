from django.db import models
from django_countries.fields import CountryField

class WorkOrganization(models.Model):
    """
    Model to store details of organizations/companies for work visa applications.
    """
    name = models.CharField(max_length=255, unique=True, help_text="Official name of the organization")
    registration_number = models.CharField(max_length=100, blank=True, null=True, help_text="Company registration or incorporation number")
    address = models.TextField(blank=True, null=True, help_text="Registered address of the organization")
    country = CountryField(help_text="Country where the organization is located")
    city = models.CharField(max_length=100, blank=True, null=True, help_text="City where the organization is located")
    website = models.URLField(blank=True, null=True, help_text="Official website of the organization")
    contact_email = models.EmailField(blank=True, null=True, help_text="Contact email for the organization")
    contact_phone = models.CharField(max_length=50, blank=True, null=True, help_text="Contact phone number")
    is_active = models.BooleanField(default=True, help_text="Is the organization currently active?")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Work Organization"
        verbose_name_plural = "Work Organizations"
        ordering = ['name']

    def __str__(self):
        return self.name
