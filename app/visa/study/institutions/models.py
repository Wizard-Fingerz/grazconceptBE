from django.db import models

# There is no built-in or prepopulated country/city data in Django by default.
# You can either:
# 1. Manually add countries and cities via the Django admin or fixtures,
# 2. Or use a third-party package like django-countries for countries (but it doesn't include cities),
# 3. Or import open datasets (e.g., from geonames.org) for more comprehensive data.

from django_countries.fields import CountryField

# class Country(models.Model):
#     code = CountryField(unique=True)

#     def __str__(self):
#         return self.code.name

# class City(models.Model):
#     name = models.CharField(max_length=100)
#     country = models.ForeignKey(Country, on_delete=models.CASCADE, related_name='cities')

#     class Meta:
#         unique_together = ('name', 'country')

#     def __str__(self):
#         return f"{self.name}, {self.country.name}"

class ProgramType(models.Model):
    name = models.CharField(max_length=100, unique=True)
    description = models.TextField(blank=True, null=True)

    def __str__(self):
        return self.name

class Institution(models.Model):
    name = models.CharField(max_length=255)
    country = CountryField()
    city = models.CharField(max_length=100)
    email_address = models.EmailField(blank=True, null=True)
    address = models.TextField(blank=True, null=True)
    website = models.URLField(blank=True, null=True)
    program_types = models.ManyToManyField(ProgramType, related_name='institutions', blank=True)

    def __str__(self):
        return self.name

class CourseOfStudy(models.Model):
    name = models.CharField(max_length=255)
    description = models.TextField(blank=True, null=True)
    institution = models.ForeignKey(Institution, on_delete=models.CASCADE, related_name='courses')
    program_type = models.ForeignKey(ProgramType, on_delete=models.CASCADE, related_name='courses')

    class Meta:
        unique_together = ('name', 'institution', 'program_type')

    def __str__(self):
        return f"{self.name} ({self.program_type.name} - {self.institution.name})"
