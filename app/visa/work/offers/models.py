from django.db import models
from django_countries.fields import CountryField
from app.visa.work.organization.models import WorkOrganization
from account.client.models import Client
from definition.models import TableDropDownDefinition
from django.conf import settings



def get_default_work_visa_status():
    try:
        return TableDropDownDefinition.objects.get(
            term="Draft",
            table_name="work_visa_application_statuses",
            is_system_defined=True
        ).id
    except Exception:
        return None

class WorkVisaOfferRequirement(models.Model):
    """
    Model to store requirements for a work visa offer.
    """
    offer = models.ForeignKey(
        'WorkVisaOffer',
        on_delete=models.CASCADE,
        related_name='requirements',
        help_text="The work visa offer this requirement belongs to"
    )
    description = models.CharField(
        max_length=255,
        help_text="Description of the requirement"
    )
    is_mandatory = models.BooleanField(
        default=True,
        help_text="Is this requirement mandatory?"
    )

    class Meta:
        verbose_name = "Work Visa Offer Requirement"
        verbose_name_plural = "Work Visa Offer Requirements"

    def __str__(self):
        return f"{self.description} ({'Mandatory' if self.is_mandatory else 'Optional'})"

class WorkVisaOffer(models.Model):
    """
    Model to store job offers for work visa applications.
    """
    organization = models.ForeignKey(
        WorkOrganization,
        on_delete=models.CASCADE,
        related_name='visa_offers',
        help_text="The organization offering the job"
    )
    job_title = models.CharField(
        max_length=255,
        help_text="Title of the job position"
    )
    job_description = models.TextField(
        blank=True,
        null=True,
        help_text="Description of the job role"
    )
    country = CountryField(
        help_text="Country where the job is located"
    )
    city = models.CharField(
        max_length=100,
        blank=True,
        null=True,
        help_text="City where the job is located"
    )
    salary = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        blank=True,
        null=True,
        help_text="Offered salary (if specified)"
    )
    currency = models.CharField(
        max_length=10,
        blank=True,
        null=True,
        help_text="Currency of the salary (e.g., USD, EUR)"
    )
    start_date = models.DateField(
        blank=True,
        null=True,
        help_text="Proposed start date for the job"
    )
    end_date = models.DateField(
        blank=True,
        null=True,
        help_text="End date of the contract (if applicable)"
    )
    is_active = models.BooleanField(
        default=True,
        help_text="Is this offer currently active?"
    )
    created_at = models.DateTimeField(
        auto_now_add=True
    )
    updated_at = models.DateTimeField(
        auto_now=True
    )

    class Meta:
        verbose_name = "Work Visa Offer"
        verbose_name_plural = "Work Visa Offers"
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.job_title} at {self.organization.name}"


def application_comment_attachment_upload_to(instance, filename):
    # Each comment's attachments go into their own directory keyed by visa app and comment id (or temp)
    comment_id = instance.id or "temp"
    visa_app_id = instance.visa_application.id if instance.visa_application_id else "temp"
    return f'work_visa/{visa_app_id}/comments/{comment_id}/{filename}'


class WorkVisaApplication(models.Model):
    """
    Model to store a client's application for a specific work visa job offer.
    The application can collect both job-related and visa-related info.
    The 'country' (nationality) is automatically filled from the client model's country.
    """
    client = models.ForeignKey(
        Client,
        on_delete=models.CASCADE,
        related_name="work_visa_applications",
        help_text="Client applying for the work visa"
    )
    offer = models.ForeignKey(
        WorkVisaOffer,
        on_delete=models.CASCADE,
        related_name="applications",
        help_text="The specific job offer the client is applying to"
    )

    # Step 1: Personal Information
    passport_number = models.CharField(
        max_length=50,
        blank=True,
        null=True,
        help_text="Applicant's passport number"
    )
    country = CountryField(
        blank=True,
        null=True,
        help_text="Applicant's nationality country (auto filled from client)"
    )
    passport_expiry_date = models.DateField(
        blank=True,
        null=True,
        help_text="Passport expiry date"
    )

    # Step 2: Job Background
    highest_degree = models.CharField(
        max_length=128,
        blank=True,
        null=True,
        help_text="Applicant's highest degree obtained"
    )
    years_of_experience = models.IntegerField(
        blank=True,
        null=True,
        help_text="Total years of work experience"
    )
    previous_employer = models.CharField(
        max_length=128,
        blank=True,
        null=True,
        help_text="Previous employer name"
    )
    previous_job_title = models.CharField(
        max_length=128,
        blank=True,
        null=True,
        help_text="Job title at previous employer"
    )
    year_left_previous_job = models.PositiveIntegerField(
        blank=True,
        null=True,
        help_text="Year applicant left previous job"
    )

    # Step 3: Work Visa Details
    intended_start_date = models.DateField(
        blank=True,
        null=True,
        help_text="Intended start date for work visa"
    )
    intended_end_date = models.DateField(
        blank=True,
        null=True,
        help_text="Intended end date for work visa"
    )
    visa_type = models.CharField(
        max_length=64,
        blank=True,
        null=True,
        help_text="Requested visa type"
    )
    sponsorship_details = models.TextField(
        blank=True,
        null=True,
        help_text="Details about sponsorship (if applicable)"
    )

    # Step 4: Document Uploads
    passport_photo = models.FileField(
        upload_to="work_visa_applications/passport_photo/",
        blank=True,
        null=True,
        help_text="Passport sized recent photo"
    )
    international_passport = models.FileField(
        upload_to="work_visa_applications/international_passport/",
        blank=True,
        null=True,
        help_text="Scanned international passport document"
    )
    updated_resume = models.FileField(
        upload_to="work_visa_applications/resume/",
        blank=True,
        null=True,
        help_text="Updated Resume/CV"
    )
    reference_letter = models.FileField(
        upload_to="work_visa_applications/reference_letter/",
        blank=True,
        null=True,
        help_text="Reference letter upload"
    )
    employment_letter = models.FileField(
        upload_to="work_visa_applications/employment_letter/",
        blank=True,
        null=True,
        help_text="Employment letter upload"
    )
    financial_statement = models.FileField(
        upload_to="work_visa_applications/financial_statement/",
        blank=True,
        null=True,
        help_text="Financial/bank statement"
    )
    english_proficiency_test = models.FileField(
        upload_to="work_visa_applications/english_proficiency/",
        blank=True,
        null=True,
        help_text="Proof of English language proficiency"
    )

    # Step 5: Additional Information
    previous_visa_applications = models.BooleanField(
        blank=True,
        null=True,
        help_text="Has applicant previously applied for a visa?"
    )
    previous_visa_details = models.TextField(
        blank=True,
        null=True,
        help_text="Details about previous visa applications"
    )
    travel_history = models.TextField(
        blank=True,
        null=True,
        help_text="Brief travel history"
    )
    emergency_contact_name = models.CharField(
        max_length=100,
        blank=True,
        null=True,
        help_text="Emergency contact name"
    )
    emergency_contact_relationship = models.CharField(
        max_length=100,
        blank=True,
        null=True,
        help_text="Relationship to emergency contact"
    )
    emergency_contact_phone = models.CharField(
        max_length=30,
        blank=True,
        null=True,
        help_text="Emergency contact phone number"
    )
    statement_of_purpose = models.TextField(
        blank=True,
        null=True,
        help_text="Applicant's statement of purpose for application"
    )

    # Deprecated/legacy fields or moved fields
    resume = models.FileField(
        upload_to='work_visa_applications/legacy_resume/',
        blank=True,
        null=True,
        help_text="(Legacy) Resume or CV document"
    )
    cover_letter = models.TextField(
        blank=True,
        null=True,
        help_text="(Legacy) Cover letter for the job application"
    )
    passport_document = models.FileField(
        upload_to='work_visa_applications/legacy_passport/',
        blank=True,
        null=True,
        help_text="(Legacy) Scanned passport document"
    )
    date_of_birth = models.DateField(
        blank=True,
        null=True,
        help_text="Applicant's date of birth"
    )
    phone_number = models.CharField(
        max_length=30,
        blank=True,
        null=True,
        help_text="Applicant's contact phone number"
    )

    # Application state
    submitted_at = models.DateTimeField(
        auto_now_add=True,
        help_text="Date/time the application was submitted"
    )

    status = models.ForeignKey(
        TableDropDownDefinition,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="work_visa_application_statuses",
        help_text="Current status of the application",
        default=get_default_work_visa_status,
    )
    
    # Optional: Note for admin or reviewer
    admin_note = models.TextField(
        blank=True,
        null=True,
        help_text="Note for internal review or admin"
    )

    class Meta:
        verbose_name = "Work Visa Application"
        verbose_name_plural = "Work Visa Applications"
        ordering = ['-submitted_at']

    def __str__(self):
        return f"Application of {self.client} for {self.offer}"

    def save(self, *args, **kwargs):
        # Auto-fill country from the client if possible
        if self.client and hasattr(self.client, "country"):
            if not self.country or self.country != self.client.country:
                self.country = self.client.country
        super().save(*args, **kwargs)


class WorkVisaApplicationComment(models.Model):
    """
    A comment/feedback on a WorkVisaApplication, for communication between admin/agent and applicant.
    """
    visa_application = models.ForeignKey(
        WorkVisaApplication,
        related_name='comments',
        on_delete=models.CASCADE,
        help_text="The Work visa application this comment belongs to."
    )
    # Either an agent/admin user or the applicant can post (applicant easiest as a Client FK, admin as User)
    applicant = models.ForeignKey(
        Client,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name='work_application_comments_sent',
        help_text="Set if this comment is from the applicant."
    )
    admin = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name='work_visa_application_comments_admin',
        help_text="Set if this comment is from an admin/agent user."
    )
    text = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    is_read_by_applicant = models.BooleanField(default=False)
    is_read_by_admin = models.BooleanField(default=False)
    # (optional) Document upload to clarify/request something
    attachment = models.FileField(
        upload_to=application_comment_attachment_upload_to,
        null=True, blank=True,
        help_text="Optional file/document related to this comment."
    )

    class Meta:
        ordering = ['created_at']

    def __str__(self):
        sender = None
        if self.applicant:
            sender = f"Applicant: {self.applicant.get_full_name() or self.applicant.user.username}"
        elif self.admin:
            sender = f"Admin: {self.admin.get_full_name() if hasattr(self.admin, 'get_full_name') else self.admin.username}"
        else:
            sender = "Unknown"
        return f"Comment by {sender} on application {self.visa_application.id}"

    @property
    def sender_type(self):
        if self.applicant and self.admin:
            return "applicant+admin"
        elif self.applicant:
            return "applicant"
        elif self.admin:
            return "admin"
        return "unknown"

    @property
    def sender_display(self):
        # For serializers/UI, show info about who sent the comment.
        if self.applicant:
            return {
                "type": "applicant",
                "name": self.applicant.get_full_name() or self.applicant.user.username,
                "id": self.applicant.id,
            }
        elif self.admin:
            return {
                "type": "admin",
                "name": self.admin.get_full_name() if hasattr(self.admin, 'get_full_name') else self.admin.username,
                "id": self.admin.id,
            }
        return {"type": "unknown"}



# class InterviewFAQ(models.Model):
#     """
#     Frequently asked questions and answers for work visa interviews.
#     """
#     question = models.CharField(max_length=250)
#     answer = models.TextField()
#     is_active = models.BooleanField(default=True)

#     class Meta:
#         verbose_name = "Interview FAQ"
#         verbose_name_plural = "Interview FAQs"

#     def __str__(self):
#         return self.question



class WorkVisaInterview(models.Model):
    """
    Stores an interview appointment for a work visa application.
    """
    STATUS_CHOICES = [
        ("Scheduled", "Scheduled"),
        ("Attending", "Attending"),
        ("Completed", "Completed"),
        ("Cancelled", "Cancelled"),
    ]

    application = models.ForeignKey(
        'WorkVisaApplication',
        on_delete=models.CASCADE,
        related_name='interviews',
        help_text="The work visa application this interview is linked to"
    )
    job_role = models.ForeignKey(
        TableDropDownDefinition,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="scheduled_interviews",
        limit_choices_to={'table_name': 'job_roles'},
        help_text="Job role for this interview"
    )
    country = CountryField(
        help_text="Country of the interview/job"
    )
    interview_date = models.DateField()
    interview_time = models.TimeField()
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default="Scheduled",
        help_text="Current interview status"
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Work Visa Interview"
        verbose_name_plural = "Work Visa Interviews"
        ordering = ['-interview_date', '-interview_time']

    def __str__(self):
        return f"{self.application.client} | {self.country} | {self.job} | {self.interview_date} {self.interview_time} ({self.status})"


class CVSubmission(models.Model):
    """
    Stores applicant's CV submissions for work visa jobs.
    """
    full_name = models.CharField(max_length=255)
    email = models.EmailField()
    phone = models.CharField(max_length=40)
    country = CountryField(help_text="Country the applicant is applying for")
    job = models.ForeignKey(
        WorkVisaOffer,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="cv_submissions",
        help_text="The job the candidate is applying for (optional if open application)",
    )
    job_title_freeform = models.CharField(
        max_length=255,
        blank=True,
        help_text="If no job is selected, applicant-supplied job name/title"
    )
    skills = models.ManyToManyField(
        TableDropDownDefinition,
        blank=True,
        limit_choices_to={'table_name': 'skills'},
        related_name="cv_submissions_with_skill",
        help_text="Skills selected from system skills list"
    )
    other_skills = models.CharField(
        max_length=400, blank=True,
        help_text="Comma separated list if applicant filled in 'other' or unlisted skills"
    )
    cv_file = models.FileField(upload_to='cv_uploads/%Y/%m/', help_text="CV file uploaded by the user")
    cover_letter = models.TextField(blank=True)
    submitted_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    is_processed = models.BooleanField(default=False, help_text="Has staff reviewed this application")

    class Meta:
        verbose_name = "CV Submission"
        verbose_name_plural = "CV Submissions"
        ordering = ['-submitted_at']

    def __str__(self):
        return f"{self.full_name} - {self.email} ({self.country}) [{self.job or self.job_title_freeform}]"

