
from django.db import models

from account.models import User
from definition.models import TableDropDownDefinition


class Client(User):
    client_type = models.ForeignKey(
        TableDropDownDefinition,
        on_delete=models.CASCADE,
        limit_choices_to={'table_name': 'client_type'},
        related_name="client_type_definition"
    )
    service_of_interest = models.ManyToManyField(
        TableDropDownDefinition,
        limit_choices_to={'table_name': 'service_of_interest'},
        related_name="client_service_of_interest"
    )
    assign_to_teams = models.ManyToManyField(
        TableDropDownDefinition,
        limit_choices_to={'table_name': 'service_of_interest'},
        related_name="client_service_of_interest_team"
    )
    internal_note_and_reminder = models.TextField(blank=True, null=True)
    country = models.CharField(max_length=100, blank=True, null=True)
    is_prospect = models.BooleanField(default=False)

    # Partner type field: only relevant for clients who are partners
    partner_type = models.ForeignKey(
        TableDropDownDefinition,
        on_delete=models.SET_NULL,
        blank=True,
        null=True,
        limit_choices_to={'table_name': 'partner_type'},
        related_name="client_partner_type",
        help_text="Only set for clients who are partners"
    )

    @property
    def client_type_name(self):
        return self.client_type.term

    @property
    def service_of_interest_names(self):
        return [s.term for s in self.service_of_interest.all()]

    @property
    def assigned_to_teams_names(self):
        return [t.term for t in self.assign_to_teams.all()]

    @property
    def partner_type_name(self):
        return self.partner_type.term if self.partner_type else None

