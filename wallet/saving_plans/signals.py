from django.db.models.signals import post_save
from django.dispatch import receiver
from decimal import Decimal

from wallet.saving_plans.models import SavingsPlan
from wallet.transactions.models import WalletTransaction
from wallet.models import Wallet

@receiver(post_save, sender=SavingsPlan)
def handle_savings_plan_one_time_deduction(sender, instance, created, **kwargs):
    """
    Perform one-time deduction for non-recurring savings plans upon their creation.
    If the plan is not recurring, is active, and has a deduction_amount, create a WalletTransaction.
    Ensure only one deduction transaction is created per plan.
    """

    # Only handle non-recurring, active plans at creation
    if not created:
        return

    plan = instance
    if (not plan.is_recurring and
        plan.status == 'active' and
        plan.deduction_amount and
        plan.deduction_amount > 0):

        # Check for existing savings funding transaction for this plan
        existing_tx = WalletTransaction.objects.filter(
            savings_plan=plan,
            transaction_type='savings_funding',
        ).first()

        if existing_tx:
            return  # Already processed

        wallet = plan.wallet
        user = plan.user

        deduction_amount = plan.deduction_amount
        if not isinstance(deduction_amount, Decimal):
            deduction_amount = Decimal(str(deduction_amount))

        # Defensive check for sufficient wallet balance
        if hasattr(wallet, "balance") and wallet.balance >= deduction_amount:
            # Deduct from wallet using WalletTransaction
            WalletTransaction.objects.create(
                user=user,
                wallet=wallet,
                transaction_type='savings_funding',
                amount=deduction_amount,
                currency=plan.currency,
                status='successful',
                reference=f"savingsfund-{plan.id}-{user.id}",
                savings_plan=plan,
                description=f"Initial funding for non-recurring savings plan '{plan.name}'",
            )

            # Update the plan's amount_saved
            plan.amount_saved = (plan.amount_saved or Decimal("0")) + deduction_amount

            # Mark as completed if target is reached
            if plan.amount_saved >= plan.target_amount:
                plan.status = 'completed'

            # Save updates
            plan.save(update_fields=["amount_saved", "status", "updated_at"])

        else:
            # Insufficient balance: Do NOT create a failed transaction, just skip
            # Optionally, could send notification here if required
            pass

