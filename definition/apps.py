from django.apps import AppConfig


class DefinitionConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'definition'

    def ready(self):
        import definition.permissions.signal
        import definition.roles.superadmin_signals
        import definition.gender.signals
        import definition.user_type.signals
        import definition.client_type.signals
        import definition.service_of_interest.signals
        import definition.document_type.signals
        import definition.hotel_reservation_status.signals

