
from django.db import models

from account.client.models import Client
from account.models import User
from definition.models import TableDropDownDefinition

from cloudinary.models import CloudinaryField

class ClientDocuments(models.Model):
    client = models.ForeignKey(Client, on_delete=models.CASCADE)
    file = CloudinaryField('file', blank=True, null=True)
    type = models.ForeignKey(TableDropDownDefinition, on_delete=models.CASCADE, related_name='client_document_type', limit_choices_to={'table_name': 'document_type'})
    uploaded_at = models.DateTimeField(auto_now_add=True)
    uploaded_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='document_uploaded_user')


    @property
    def type_term(self):
        return self.type.term

    @property
    def client_name(self):
        return f"{self.client.first_name} {self.client.last_name}".strip()