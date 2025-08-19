from django.db import models

# Create your models here.

class TableDropDownDefinition(models.Model):
    term = models.CharField(max_length=200)
    table_name = models.CharField(max_length=200)
    is_active = models.BooleanField(default=True)
    is_system_defined = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)


    def __str__(self):
        return self.term