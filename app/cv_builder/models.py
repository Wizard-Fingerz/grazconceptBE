from django.db import models
from django_countries.fields import CountryField
from cloudinary.models import CloudinaryField

from account.models import User


class CVProfile(models.Model):
    """
    Main model representing a CV/profile information for a user.
    Designed to support professional & academic CVs.
    The owner is also the user.
    """
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    # The 'owner' field is removed; use 'user' as owner.
    summary = models.TextField(blank=True)
    photo = CloudinaryField('image', blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.user.full_name} (CV)"


class CVEducation(models.Model):
    """
    Education entry belonging to a CVProfile.
    """
    cv = models.ForeignKey(
        CVProfile, on_delete=models.CASCADE, related_name='education')
    institution = models.CharField(max_length=200)
    degree = models.CharField(max_length=120)
    field = models.CharField(max_length=120)
    start_year = models.CharField(max_length=12)
    end_year = models.CharField(max_length=12, blank=True)
    grade = models.CharField(max_length=50, blank=True)
    description = models.TextField(blank=True)

    def __str__(self):
        return f"{self.degree} in {self.field} at {self.institution}"


class CVExperience(models.Model):
    """
    Work/Professional experience for a CVProfile.
    """
    cv = models.ForeignKey(
        CVProfile, on_delete=models.CASCADE, related_name='experience')
    organization = models.CharField(max_length=200)
    position = models.CharField(max_length=120)
    start_month = models.CharField(max_length=20)
    start_year = models.CharField(max_length=12)
    end_month = models.CharField(max_length=20, blank=True)
    end_year = models.CharField(max_length=12, blank=True)
    location = models.CharField(max_length=120, blank=True)
    description = models.TextField(blank=True)
    current = models.BooleanField(default=False)

    def __str__(self):
        return f"{self.position} at {self.organization}"


class CVCertification(models.Model):
    """
    Certifications (professional or academic) for a CVProfile.
    """
    cv = models.ForeignKey(
        CVProfile, on_delete=models.CASCADE, related_name='certifications')
    name = models.CharField(max_length=150)
    issuer = models.CharField(max_length=120, blank=True)
    issue_month = models.CharField(max_length=20, blank=True)
    issue_year = models.CharField(max_length=12)
    description = models.TextField(blank=True)

    def __str__(self):
        return f"{self.name} ({self.issuer})"


class CVSkill(models.Model):
    """
    Represents a single skill for a CVProfile.
    """
    cv = models.ForeignKey(
        CVProfile, on_delete=models.CASCADE, related_name='skills')
    skill = models.CharField(max_length=100)

    def __str__(self):
        return self.skill


class CVLanguage(models.Model):
    """
    Represents a language and proficiency for a CVProfile.
    """
    PROFICIENCY_LEVELS = [
        ("Native", "Native"),
        ("Fluent", "Fluent"),
        ("Professional Working", "Professional Working"),
        ("Conversational", "Conversational"),
        ("Basic", "Basic"),
    ]
    cv = models.ForeignKey(
        CVProfile, on_delete=models.CASCADE, related_name='languages')
    name = models.CharField(max_length=60)
    proficiency = models.CharField(max_length=32, choices=PROFICIENCY_LEVELS)

    def __str__(self):
        return f"{self.name} ({self.proficiency})"


class CVPublication(models.Model):
    """
    Publications (journal/conference/thesis) for a CVProfile.
    """
    cv = models.ForeignKey(
        CVProfile, on_delete=models.CASCADE, related_name='publications')
    title = models.CharField(max_length=255)
    journal = models.CharField(max_length=180, blank=True)
    year = models.CharField(max_length=8, blank=True)
    link = models.URLField(blank=True)
    description = models.TextField(blank=True)

    def __str__(self):
        return self.title
