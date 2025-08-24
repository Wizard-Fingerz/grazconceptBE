
from django.db import models

from account.models import User
from definition.models import TableDropDownDefinition



class Client(User):
    client_type = models.ForeignKey(TableDropDownDefinition, on_delete=models.CASCADE, limit_choices_to={'type': 'client_type'}, related_name="client_type_definition")
    service_of_interest = models.ManyToManyField(TableDropDownDefinition, limit_choices_to={'type': 'service_of_interest'}, related_name="client_service_of_interest")
    assign_to_teams = models.ManyToManyField(TableDropDownDefinition, limit_choices_to={'type': 'service_of_interest'}, related_name="client_service_of_interest_team")
    internal_note_and_reminder = models.TextField(blank = True, null = True)



