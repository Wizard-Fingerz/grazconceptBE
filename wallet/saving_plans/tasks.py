import datetime
from django.utils import timezone
from django.conf import settings
from decimal import Decimal

from wallet.saving_plans.models import SavingsPlan
from wallet.models import Wallet
from notification.models import Notification

from celery import shared_task

# --- Utility function for notifications (as in notification/saving_plans/signals.py) ---
def create_savings_plan_notification(user, title, message, notification_type="saving_plan", data=None):
    Notification.objects.create(
        user=user,
        title=title,
        message=message,
        notification_type=notification_type,
        data=data or {},
    )

@shared_task
def process_recurring_savings_plans():
    """
    Deducts the recurring amount from user wallets for all active, recurring savings plans
    that are due for deduction based on their period, and sends notifications for success/failure.
    This is intended to run as a Celery periodic/background task.
    """
    today = timezone.now().date()
    # Fetch all active, recurring savings plans where today is within the plan's date range
    plans = SavingsPlan.objects.filter(
        is_recurring=True,
        status='active',
        start_date__lte=today,
        end_date__gte=today,
        deduction_amount__isnull=False
    ).select_related('wallet', 'user')

    for plan in plans:
        # Determine if today is a deduction day for this plan
        last_deduction_date = getattr(plan, 'meta', {}).get('last_deduction_date')
        should_deduct = False

        if plan.recurrence_period == "daily":
            should_deduct = (last_deduction_date is None) or (str(today) > last_deduction_date)
        elif plan.recurrence_period == "weekly":
            # Deduct if it's the correct weekday and last_deduction_date < today
            start_weekday = plan.start_date.weekday()
            if today.weekday() == start_weekday:
                should_deduct = (last_deduction_date is None) or (str(today) > last_deduction_date)
        elif plan.recurrence_period == "monthly":
            # Deduct if it's the right day of the month (or if the plan started on 29-31 and today is last day of month)
            plan_dom = plan.start_date.day
            try:
                recurring_dom = plan_dom
                last_dom = (today.replace(day=28) + datetime.timedelta(days=4)).day
                if plan_dom > 28:
                    # For plans started on 29-31, only run deduction if today is the last day of month
                    next_day = today + datetime.timedelta(days=1)
                    is_last_day = next_day.month != today.month
                    recurring_dom = today.day if is_last_day else plan_dom
                if today.day == recurring_dom:
                    should_deduct = (last_deduction_date is None) or (str(today) > last_deduction_date)
            except Exception:
                pass

        if not should_deduct:
            continue

        # Proceed with deduction from wallet
        wallet = plan.wallet
        deduction_amount = plan.deduction_amount
        # Defensive: ensure these are Decimal
        if not isinstance(deduction_amount, Decimal):
            deduction_amount = Decimal(str(deduction_amount))
        if not hasattr(wallet, 'balance'):
            # Wallet implementation without balance: skip with notification
            create_savings_plan_notification(
                user=plan.user,
                title="Recurring Savings Deduction Failed",
                message=f"Your wallet is not properly configured for savings plan '{plan.name}'. Please contact support.",
                notification_type="saving_plan",
                data={
                    "event": "wallet_not_configured",
                    "plan_id": plan.id,
                    "name": plan.name,
                }
            )
            continue

        if wallet.balance >= deduction_amount:
            # Deduct from wallet and update amount_saved
            wallet.balance -= deduction_amount
            wallet.save(update_fields=["balance"])
            plan.amount_saved += deduction_amount
            # Mark the new last_deduction_date
            if not plan.meta:
                plan.meta = {}
            plan.meta['last_deduction_date'] = str(today)
            # Mark plan as completed if fully funded
            if plan.amount_saved >= plan.target_amount:
                plan.status = 'completed'
            plan.save(update_fields=["amount_saved", "meta", "status", "updated_at"])
            # Send notification for successful deduction
            create_savings_plan_notification(
                user=plan.user,
                title="Recurring Savings Deducted",
                message=(
                    f"{deduction_amount} {plan.currency} has been deducted from your wallet "
                    f"for the savings plan '{plan.name}'. "
                    f"Total saved: {plan.amount_saved} {plan.currency}."
                ),
                notification_type="saving_plan",
                data={
                    "event": "recurring_deduction_success",
                    "plan_id": plan.id,
                    "deducted_amount": str(deduction_amount),
                    "name": plan.name,
                    "amount_saved": str(plan.amount_saved),
                    "target_amount": str(plan.target_amount),
                    "currency": plan.currency,
                }
            )
            if plan.status == 'completed':
                # Extra notification for completion (in case signals don't fire)
                create_savings_plan_notification(
                    user=plan.user,
                    title="Savings Plan Completed",
                    message=f"Congratulations! Your savings plan '{plan.name}' has reached its target.",
                    notification_type="saving_plan",
                    data={
                        "event": "savings_plan_completed",
                        "plan_id": plan.id,
                        "name": plan.name,
                        "amount_saved": str(plan.amount_saved),
                        "target_amount": str(plan.target_amount),
                        "currency": plan.currency,
                    }
                )
        else:
            # Insufficient funds; move on and notify user
            create_savings_plan_notification(
                user=plan.user,
                title="Recurring Savings Deduction Failed",
                message=(
                    f"Unable to deduct {deduction_amount} {plan.currency} "
                    f"for your savings plan '{plan.name}' due to insufficient wallet balance. "
                    f"Please fund your wallet to continue your savings plan."
                ),
                notification_type="saving_plan",
                data={
                    "event": "recurring_deduction_failed_insufficient_balance",
                    "plan_id": plan.id,
                    "attempted_deduction": str(deduction_amount),
                    "wallet_balance": str(wallet.balance),
                    "name": plan.name,
                    "currency": plan.currency,
                }
            )


            # Guide: Configuring Celery for Django & Deploying on Render

            # 1. Install dependencies (add to requirements.txt):
            # celery
            # redis (or other broker)

            # 2. In your Django project (e.g., project/celery.py):
            #
            # import os
            # from celery import Celery
            #
            # os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'your_project.settings')
            # app = Celery('your_project')
            # app.config_from_object('django.conf:settings', namespace='CELERY')
            # app.autodiscover_tasks()

            # 3. In your settings.py, add configurations:
            #
            # CELERY_BROKER_URL = os.environ.get("REDIS_URL", "redis://localhost:6379/0")
            # CELERY_RESULT_BACKEND = os.environ.get("REDIS_URL", "redis://localhost:6379/0")
            # CELERY_ACCEPT_CONTENT = ["json"]
            # CELERY_TASK_SERIALIZER = "json"
            # CELERY_RESULT_SERIALIZER = "json"
            # CELERY_TIMEZONE = "UTC"
            #
            # Make sure to import os at the top of settings.py

            # 4. In your __init__.py for the Django project (same directory as settings.py), add:
            #
            # from .celery import app as celery_app
            # __all__ = ["celery_app"]

            # 5. Add scheduled (periodic) tasks (optionally in settings.py or using Django-Celery-Beat):
            #
            # CELERY_BEAT_SCHEDULE = {
            #     "process-recurring-savings-plans": {
            #         "task": "wallet.saving_plans.tasks.process_recurring_savings_plans",
            #         "schedule": 86400.0,  # Every day (in seconds). Adjust as needed.
            #     },
            # }

            # --- Deploying Celery on Render.com ---

            # 6. Add a Redis instance from Render as your broker and get the REDIS_URL from your Render dashboard.

            # 7. In your Render service, add background workers:
            #
            # (a) Celery Worker:
            #    Type: Worker
            #    Start Command:
            #        celery -A globalconceptBE worker --loglevel=info
            #
            # (b) Celery Beat (for periodic tasks):
            #    Type: Worker
            #    Start Command:
            #        celery -A globalconceptBE beat --loglevel=info

            # 8. Ensure the REDIS_URL environment variable is set for both Django (web) and the workers.

            # 9. If you run your server with Daphne, a typical command is:
            #        daphne -b 0.0.0.0 -p 8002 globalconceptBE.asgi:application
            #    Make sure both your Django app (Daphne or WSGI) and Celery workers point to the same codebase and environment.

            # For more details, see:
            # - https://docs.celeryq.dev/en/stable/django/first-steps-with-django.html
            # - https://render.com/docs/background-workers
            # - https://render.com/docs/redis

