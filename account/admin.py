from django.contrib import admin

from import_export import resources
from import_export.admin import ImportExportModelAdmin

from account.client.documents.models import ClientDocuments
from account.client.models import Client

from .models import User

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



admin.site.site_title = "GrazConcept Admin Dashboard"
admin.site.site_header = "Account Administration"
