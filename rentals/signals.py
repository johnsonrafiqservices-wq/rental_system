from django.db.models.signals import post_save
from django.dispatch import receiver


@receiver(post_save, sender='rentals.Rental')
def auto_generate_invoices(sender, instance, **kwargs):
    """
    Auto-generate invoices for a rental whenever it has a tenant and is active.
    The generator is idempotent — existing invoice periods are never duplicated.
    """
    if instance.tenant and instance.status == 'active':
        from billing.utils import generate_invoices_for_rental
        generate_invoices_for_rental(instance)
