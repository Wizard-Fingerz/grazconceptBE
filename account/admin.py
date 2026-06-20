from django.contrib import admin
from import_export import resources
from import_export.admin import ImportExportModelAdmin
from account.client.documents.models import ClientDocuments
from account.client.models import Client
from .models import User, UserProfile


class UserResource(resources.ModelResource):
    class Meta:
        model = User


class ClientResource(resources.ModelResource):
    class Meta:
        model = Client


class ClientDocumentsResource(resources.ModelResource):
    class Meta:
        model = ClientDocuments


@admin.register(User)
class UserAdmin(ImportExportModelAdmin):
    resource_class = UserResource


@admin.register(Client)
class ClientAdmin(ImportExportModelAdmin):
    resource_class = ClientResource


@admin.register(ClientDocuments)
class ClientDocumentsAdmin(ImportExportModelAdmin):
    resource_class = ClientDocumentsResource


@admin.register(UserProfile)
class UserProfileAdmin(admin.ModelAdmin):
    list_display = ['user', 'passport_number', 'highest_qualification', 'previous_job_title', 'updated_at']
    search_fields = ['user__email', 'user__first_name', 'user__last_name', 'passport_number']
    raw_id_fields = ['user']
    readonly_fields = ['created_at', 'updated_at']
    fieldsets = (
        ('User', {'fields': ('user',)}),
        ('Identity', {'fields': ('passport_number', 'passport_expiry_date', 'nin', 'bvn')}),
        ('Education', {'fields': ('highest_qualification', 'graduation_year', 'previous_university', 'previous_course_of_study', 'cgpa')}),
        ('Employment', {'fields': ('previous_job_title', 'previous_employer', 'years_of_experience', 'year_left_previous_job')}),
        ('Emergency', {'fields': ('emergency_contact_name', 'emergency_contact_relationship', 'emergency_contact_phone')}),
        ('Travel', {'fields': ('travel_history', 'previous_visa_applications', 'previous_visa_details')}),
        ('Timestamps', {'fields': ('created_at', 'updated_at'), 'classes': ('collapse',)}),
    )


admin.site.site_title = "GrazConcept Admin Dashboard"
admin.site.site_header = "Account Administration"
