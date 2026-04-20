from datetime import date, timedelta
from dateutil.relativedelta import relativedelta


def generate_invoices_for_rental(rental):
    """
    Generate Invoice objects for every due period that does not yet have one.
    Safe to call multiple times — skips periods that already have an invoice.
    Returns a list of newly created Invoice objects.
    """
    from .models import Invoice

    freq = rental.payment_frequency
    today = date.today()
    end = rental.end_date or today

    if freq == 'weekly':
        delta = relativedelta(weeks=1)
    elif freq == 'quarterly':
        delta = relativedelta(months=3)
    elif freq == 'annually':
        delta = relativedelta(years=1)
    else:  # monthly (default)
        delta = relativedelta(months=1)

    created = []
    period_start = rental.start_date

    while period_start <= min(end, today):
        period_end = period_start + delta - timedelta(days=1)
        due_date = period_start + delta

        exists = Invoice.objects.filter(
            rental=rental,
            period_start=period_start
        ).exists()

        if not exists:
            invoice = Invoice.objects.create(
                rental=rental,
                period_start=period_start,
                period_end=period_end,
                rent_amount=rental.monthly_rent,
                currency=rental.currency,
                issue_date=period_start,
                due_date=due_date,
                status='sent',
            )
            created.append(invoice)

        period_start += delta

    return created
