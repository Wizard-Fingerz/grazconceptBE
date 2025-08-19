from django.db import models
    
class UserPermissions(models.Model):
    name = models.CharField(max_length=2000, unique=True)
    is_system_defined = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    
    def save(self, *args, **kwargs):
        # self.name = self.name.lower() 
        super(UserPermissions, self).save(*args, **kwargs)

    def __str__(self):
        return self.name
    

class Modules(models.Model):
    name = models.CharField(max_length=2000, unique=True)
    created_at= models.DateTimeField(auto_now_add=True)
    is_system_defined = models.BooleanField(default=False)
    permissions = models.ManyToManyField(UserPermissions, related_name="modules", blank=True,
        help_text="User permissions associated with this module"
    )

    def to_json(self):
        return {
            'id': self.id,
            'name': self.name,
            'permissions': [
                {'id': permission.id, 'name': permission.name} for permission in self.permissions.all()
            ],
        }

    def __str__(self):
        return self.name
