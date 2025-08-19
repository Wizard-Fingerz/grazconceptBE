from django.db import models
from ..permissions.models import UserPermissions, Modules
import random
import string


class Roles(models.Model):
    name = models.CharField(max_length=500, unique=True)
    #permissions = models.ManyToManyField(UserPermissions, related_name='user_permissions')
    modules = models.ManyToManyField(Modules, related_name="roles", blank=True, help_text="Modules associated with this role")
    is_active = models.BooleanField(default=True)
    is_deleted=models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    custom_id = models.CharField(max_length=20, unique=True, null=True, blank=True)
    
    def to_json(self):
        return {
            'id': self.id,
            'name': self.name,
            # 'modules': [
            #     module.to_json() for module in self.modules.all()
            # ]
        }
   
    def delete(self, *args, **kwargs):
        self.is_deleted = True
        self.save()
        
    def restore(self):
        self.is_deleted = False
        self.save()

    def save(self, *args, **kwargs):
        if not self.custom_id:  
            self.custom_id = generate_custom_id()
        super(Roles, self).save(*args, **kwargs)
    
    def __str__(self):
        return self.name



def generate_custom_id():
        numbers_part = ''.join(random.choice('0123456789') for _ in range(6))
        letters_part = ''.join(random.choice(string.ascii_uppercase) for _ in range(2))
        
        custom_id = numbers_part + letters_part
        return custom_id


    
    