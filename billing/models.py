from django.db import models
from django.core.validators import MinValueValidator
from django.urls import reverse
from rentals.models import Rental, CURRENCY_CHOICES
import uuid
from datetime import date


class Invoice(models.Model):
    """Invoice generated for a rental period"""
    STATUS_CHOICES = (
        ('draft', 'Draft'),
        ('sent', 'Sent'),
        ('paid', 'Paid'),
        ('partially_paid', 'Partially Paid'),
        ('overdue', 'Overdue'),
        ('cancelled', 'Cancelled'),
    )

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    invoice_number = models.CharField(max_length=50, unique=True, editable=False)
    rental = models.ForeignKey(Rental, on_delete=models.CASCADE, related_name='invoices')

    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='draft')

    # Billing period
    period_start = models.DateField()
    period_end = models.DateField()

    # Amounts
    rent_amount = models.DecimalField(max_digits=12, decimal_places=2, validators=[MinValueValidator(0)])
    tax_amount = models.DecimalField(max_digits=12, decimal_places=2, default=0, validators=[MinValueValidator(0)])
    additional_charges = models.DecimalField(max_digits=12, decimal_places=2, default=0, validators=[MinValueValidator(0)])
    discount = models.DecimalField(max_digits=12, decimal_places=2, default=0, validators=[MinValueValidator(0)])
    currency = models.CharField(max_length=3, choices=CURRENCY_CHOICES, default='UGX')

    # Dates
    issue_date = models.DateField(default=date.today)
    due_date = models.DateField()

    notes = models.TextField(blank=True, null=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-issue_date', '-created_at']

    @property
    def total_amount(self):
        return self.rent_amount + self.tax_amount + self.additional_charges - self.discount

    @property
    def amount_paid(self):
        return sum(p.amount for p in self.payments.filter(status='completed'))

    @property
    def balance_due(self):
        return self.total_amount - self.amount_paid

    @property
    def is_overdue(self):
        return self.status not in ('paid', 'cancelled') and self.due_date < date.today()

    @property
    def payment_percentage(self):
        if self.total_amount == 0:
            return 100
        return min(round((self.amount_paid / self.total_amount) * 100), 100)

    def get_absolute_url(self):
        return reverse('billing:invoice_detail', kwargs={'pk': self.pk})

    def update_status(self):
        """Auto-update status based on payments"""
        if self.status == 'cancelled':
            return
        paid = self.amount_paid
        total = self.total_amount
        if paid >= total:
            self.status = 'paid'
        elif paid > 0:
            self.status = 'partially_paid'
        elif self.is_overdue:
            self.status = 'overdue'
        self.save(update_fields=['status'])

    def save(self, *args, **kwargs):
        if not self.invoice_number:
            last = Invoice.objects.order_by('-created_at').first()
            if last and last.invoice_number.startswith('INV-'):
                try:
                    num = int(last.invoice_number.split('-')[1]) + 1
                except (ValueError, IndexError):
                    num = 1
            else:
                num = 1
            self.invoice_number = f'INV-{num:06d}'
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.invoice_number} - {self.rental.property_obj.name}"


class Payment(models.Model):
    """Payment made against an invoice"""
    METHOD_CHOICES = (
        ('cash', 'Cash'),
        ('bank_transfer', 'Bank Transfer'),
        ('mobile_money', 'Mobile Money'),
        ('cheque', 'Cheque'),
        ('card', 'Card'),
        ('other', 'Other'),
    )
    STATUS_CHOICES = (
        ('pending', 'Pending'),
        ('completed', 'Completed'),
        ('failed', 'Failed'),
        ('refunded', 'Refunded'),
    )

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    receipt_number = models.CharField(max_length=50, unique=True, editable=False)
    invoice = models.ForeignKey(Invoice, on_delete=models.CASCADE, related_name='payments')

    amount = models.DecimalField(max_digits=12, decimal_places=2, validators=[MinValueValidator(0)])
    currency = models.CharField(max_length=3, choices=CURRENCY_CHOICES, default='UGX')

    payment_method = models.CharField(max_length=20, choices=METHOD_CHOICES, default='cash')
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='completed')

    payment_date = models.DateField(default=date.today)
    reference = models.CharField(max_length=255, blank=True, null=True, help_text='Transaction reference or cheque number')
    notes = models.TextField(blank=True, null=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-payment_date', '-created_at']

    def get_absolute_url(self):
        return reverse('billing:payment_detail', kwargs={'pk': self.pk})

    def save(self, *args, **kwargs):
        if not self.receipt_number:
            last = Payment.objects.order_by('-created_at').first()
            if last and last.receipt_number.startswith('RCP-'):
                try:
                    num = int(last.receipt_number.split('-')[1]) + 1
                except (ValueError, IndexError):
                    num = 1
            else:
                num = 1
            self.receipt_number = f'RCP-{num:06d}'
        super().save(*args, **kwargs)
        # Auto-update invoice status after payment
        self.invoice.update_status()

    def __str__(self):
        return f"{self.receipt_number} - {self.amount} {self.currency}"


class Budget(models.Model):
    """Annual or monthly budget for the rental business"""
    PERIOD_CHOICES = (
        ('monthly', 'Monthly'),
        ('quarterly', 'Quarterly'),
        ('yearly', 'Yearly'),
    )
    STATUS_CHOICES = (
        ('draft', 'Draft'),
        ('active', 'Active'),
        ('closed', 'Closed'),
    )

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=200)
    period_type = models.CharField(max_length=20, choices=PERIOD_CHOICES, default='monthly')
    start_date = models.DateField()
    end_date = models.DateField()
    currency = models.CharField(max_length=3, choices=CURRENCY_CHOICES, default='UGX')
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='draft')
    notes = models.TextField(blank=True, null=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-start_date']

    @property
    def total_budgeted(self):
        return sum(item.amount for item in self.items.all())

    @property
    def total_spent(self):
        return sum(item.spent for item in self.items.all())

    @property
    def remaining(self):
        return self.total_budgeted - self.total_spent

    @property
    def utilization_percentage(self):
        if self.total_budgeted == 0:
            return 0
        return round((self.total_spent / self.total_budgeted) * 100, 1)

    def __str__(self):
        return f"{self.name} ({self.get_period_type_display()})"


class BudgetItem(models.Model):
    """Individual budget category within a budget"""
    CATEGORY_CHOICES = (
        ('maintenance', 'Maintenance & Repairs'),
        ('utilities', 'Utilities'),
        ('insurance', 'Insurance'),
        ('taxes', 'Taxes & Licenses'),
        ('marketing', 'Marketing & Advertising'),
        ('salaries', 'Staff Salaries'),
        ('supplies', 'Office Supplies'),
        ('legal', 'Legal & Professional'),
        ('cleaning', 'Cleaning Services'),
        ('security', 'Security'),
        ('other', 'Other'),
    )

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    budget = models.ForeignKey(Budget, on_delete=models.CASCADE, related_name='items')
    category = models.CharField(max_length=30, choices=CATEGORY_CHOICES)
    description = models.CharField(max_length=255)
    amount = models.DecimalField(max_digits=12, decimal_places=2, validators=[MinValueValidator(0)])

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['category', 'description']

    @property
    def spent(self):
        """Total expenses recorded against this budget item"""
        return sum(exp.amount for exp in self.expenses.filter(status='approved'))

    @property
    def remaining(self):
        return self.amount - self.spent

    @property
    def utilization_percentage(self):
        if self.amount == 0:
            return 0
        return round((self.spent / self.amount) * 100, 1)

    def __str__(self):
        return f"{self.get_category_display()} - {self.description}"


class Expense(models.Model):
    """Expense recorded against a budget"""
    STATUS_CHOICES = (
        ('draft', 'Draft'),
        ('submitted', 'Submitted'),
        ('approved', 'Approved'),
        ('rejected', 'Rejected'),
        ('paid', 'Paid'),
    )
    EXPENSE_TYPE_CHOICES = (
        ('operational', 'Operational'),
        ('capital', 'Capital Expenditure'),
        ('emergency', 'Emergency'),
        ('planned', 'Planned'),
    )

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    expense_number = models.CharField(max_length=50, unique=True, editable=False)
    budget_item = models.ForeignKey(BudgetItem, on_delete=models.CASCADE, related_name='expenses', null=True, blank=True)
    
    # Can also be linked to a property or rental directly
    property_obj = models.ForeignKey('rentals.Property', on_delete=models.CASCADE, related_name='expenses', null=True, blank=True)
    rental = models.ForeignKey('rentals.Rental', on_delete=models.CASCADE, related_name='expenses', null=True, blank=True)

    expense_type = models.CharField(max_length=20, choices=EXPENSE_TYPE_CHOICES, default='operational')
    description = models.CharField(max_length=255)
    amount = models.DecimalField(max_digits=12, decimal_places=2, validators=[MinValueValidator(0)])
    currency = models.CharField(max_length=3, choices=CURRENCY_CHOICES, default='UGX')

    vendor_name = models.CharField(max_length=200, blank=True, null=True)
    invoice_number = models.CharField(max_length=100, blank=True, null=True)
    expense_date = models.DateField(default=date.today)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='draft')

    receipt_file = models.FileField(upload_to='expenses/receipts/', blank=True, null=True)
    notes = models.TextField(blank=True, null=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-expense_date', '-created_at']

    def save(self, *args, **kwargs):
        if not self.expense_number:
            last = Expense.objects.order_by('-created_at').first()
            if last and last.expense_number.startswith('EXP-'):
                try:
                    num = int(last.expense_number.split('-')[1]) + 1
                except (ValueError, IndexError):
                    num = 1
            else:
                num = 1
            self.expense_number = f'EXP-{num:06d}'
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.expense_number} - {self.description} ({self.amount} {self.currency})"
