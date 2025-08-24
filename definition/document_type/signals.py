from django.db.models.signals import post_migrate
from django.dispatch import receiver
import os

from definition.models import TableDropDownDefinition
from django.db import IntegrityError

@receiver(post_migrate)
def create_system_defined_entries(sender, **kwargs):
    if sender.name == 'app':
        file_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'system_defined_definitions.txt')
        with open(file_path, 'r') as file:
            for line in file:
                name = line.strip()
                try:
                    TableDropDownDefinition.objects.get_or_create(
                        term=name,
                        table_name='document_type',
                        is_system_defined=True,
                        defaults={'is_system_defined': True}
                    )
                except IntegrityError:
                    pass
                #gender, created = Gender.objects.get_or_create(name=name)
                #if not gender.is_system_defined:
                #    gender.is_system_defined = True
                #    gender.save()
