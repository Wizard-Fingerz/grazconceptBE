from django.db.models.signals import post_migrate
from django.dispatch import receiver
import os
from .models import Modules, UserPermissions
from django.db import IntegrityError

@receiver(post_migrate)
def create_system_defined_entries(sender, **kwargs):
    if sender.name == 'app':
        file_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'system_defined_permissions_definitions.txt')
        with open(file_path, 'r') as file:
            for line in file:
                name = line.strip()
                try:
                    UserPermissions.objects.get_or_create(
                        name=name,
                        is_system_defined=True,
                        defaults={'is_system_defined': True}
                    )
                except IntegrityError:
                    pass
                #UserPermissions.objects.get_or_create(
                #    name=name
                #)


@receiver(post_migrate)
def create_system_defined_permission_modules_entries(sender, **kwargs):
    if sender.name == 'app':
        file_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'system_defined_permissions_module_definition.txt')
        with open(file_path, 'r') as file:
            for line in file:
                name = line.strip()
                try:
                    Modules.objects.get_or_create(
                        name=name,
                        is_system_defined=True,
                        defaults={'is_system_defined': True}
                   
                    )
                except IntegrityError:
                    pass

