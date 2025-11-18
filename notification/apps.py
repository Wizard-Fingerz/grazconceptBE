from django.apps import AppConfig


class NotificationConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'notification'


    def ready(self):
        import notification.wallet.signals
        import notification.saving_plans.signals
        import notification.visa.work.signals
        import notification.visa.vacation.signals
        import notification.visa.study.signals