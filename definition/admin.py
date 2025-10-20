from django.contrib import admin

# Register your models here.
from django.contrib import admin
from .models import TableDropDownDefinition

@admin.register(TableDropDownDefinition)
class TableDropDownDefinitionAdmin(admin.ModelAdmin):
    list_display = ('table_name', 'term', 'is_active', 'is_system_defined', 'created_at')
    search_fields = ('table_name', 'term', 'is_active', 'is_system_defined')
    ordering = ('table_name','term')
    list_filter = ('table_name', 'created_at')

