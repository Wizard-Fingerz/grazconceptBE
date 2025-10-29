# signals.py
import os
from django.db.models.signals import post_migrate
from django.dispatch import receiver
from django.conf import settings
from .models import InvestmentOption

@receiver(post_migrate)
def create_investment_options(sender, **kwargs):
    """
    Auto-populate InvestmentOption entries from a .txt file
    after migrations.
    """
    file_path = os.path.join(settings.BASE_DIR, 'app', 'citizenship', 'european', 'investment_options.txt')

    if not os.path.exists(file_path):
        print(f"[InvestmentOption] Data file not found: {file_path}")
        return

    with open(file_path, 'r', encoding='utf-8') as file:
        for line in file:
            parts = line.strip().split('|')
            if len(parts) >= 2:
                type_name = parts[0]
                min_amount = int(parts[1])
                amount_field = parts[2] if len(parts) > 2 and parts[2] else None
                amount_label = parts[3] if len(parts) > 3 and parts[3] else None

                obj, created = InvestmentOption.objects.get_or_create(
                    type=type_name,
                    defaults={
                        'min_amount': min_amount,
                        'amount_field': amount_field,
                        'amount_label': amount_label
                    }
                )
                if created:
                    print(f"[InvestmentOption] Created: {type_name}")
