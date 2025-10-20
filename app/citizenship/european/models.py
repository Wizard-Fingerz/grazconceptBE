from django.db import models
from django_countries.fields import CountryField

class EuropeanCitizenshipOffer(models.Model):
    country = CountryField(help_text="Country offering the citizenship program")
    quote = models.TextField(blank=True, help_text="A brief promotional or descriptive quote about this program")
    type = models.CharField(max_length=100, help_text="Type or category of citizenship offer (e.g., Investment, Ancestry, Naturalization)")
    description = models.TextField(blank=True, help_text="Detailed description about the process and benefits of the citizenship offer")
    minimum_investment = models.CharField(max_length=100, help_text="Minimum investment required, if applicable. E.g., '€250,000' or 'N/A'")
    visa_free_access = models.CharField(max_length=200, help_text="Number or list of countries accessible visa-free")
    dual_citizenship = models.CharField(max_length=20, help_text="Whether dual citizenship is permitted")
    requirements = models.TextField(blank=True, help_text="Documents, criteria, or eligibility requirements for this offer")
    processing_time = models.CharField(max_length=100, blank=True, help_text="Estimated time required to process citizenship")
    government_fees = models.CharField(max_length=100, blank=True, help_text="Government and/or processing fees")
    family_inclusion = models.CharField(max_length=200, blank=True, help_text="Rules on inclusion of family members, dependents, spouse etc")
    benefits = models.TextField(blank=True, help_text="List of other benefits provided by this offer (e.g. education, healthcare, tax incentives)")

    flag_url = models.URLField(blank=True, help_text="URL of the country flag")
    gradient = models.CharField(max_length=200, blank=True, null=True, help_text="Optional CSS linear-gradient or color string for background")

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "European Citizenship Offer"
        verbose_name_plural = "European Citizenship Offers"

    def __str__(self):
        return f"{self.country} - {self.type}"

