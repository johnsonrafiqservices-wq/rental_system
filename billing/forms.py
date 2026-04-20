from django import forms
from .models import Invoice, Payment, Budget, BudgetItem, Expense
from rentals.models import Rental, Property, CURRENCY_CHOICES


class InvoiceForm(forms.ModelForm):
    class Meta:
        model = Invoice
        fields = [
            'rental', 'period_start', 'period_end',
            'rent_amount', 'tax_amount', 'additional_charges', 'discount',
            'currency', 'issue_date', 'due_date', 'notes',
        ]
        widgets = {
            'rental': forms.Select(attrs={'class': 'form-select'}),
            'period_start': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'period_end': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'rent_amount': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'tax_amount': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'additional_charges': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'discount': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'currency': forms.Select(attrs={'class': 'form-select'}),
            'issue_date': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'due_date': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'notes': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
        }

    def __init__(self, *args, **kwargs):
        rental_id = kwargs.pop('rental_id', None)
        super().__init__(*args, **kwargs)
        self.fields['rental'].queryset = Rental.objects.filter(status__in=['active', 'pending']).select_related('property_obj', 'tenant')
        if rental_id:
            self.fields['rental'].initial = rental_id


class PaymentForm(forms.ModelForm):
    class Meta:
        model = Payment
        fields = [
            'invoice', 'amount', 'currency', 'payment_method',
            'status', 'payment_date', 'reference', 'notes',
        ]
        widgets = {
            'invoice': forms.Select(attrs={'class': 'form-select'}),
            'amount': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'currency': forms.Select(attrs={'class': 'form-select'}),
            'payment_method': forms.Select(attrs={'class': 'form-select'}),
            'status': forms.Select(attrs={'class': 'form-select'}),
            'payment_date': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'reference': forms.TextInput(attrs={'class': 'form-control'}),
            'notes': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
        }

    def __init__(self, *args, **kwargs):
        invoice_id = kwargs.pop('invoice_id', None)
        super().__init__(*args, **kwargs)
        self.fields['invoice'].queryset = Invoice.objects.exclude(status__in=['paid', 'cancelled']).select_related('rental__property_obj', 'rental__tenant')
        if invoice_id:
            self.fields['invoice'].initial = invoice_id


class BudgetForm(forms.ModelForm):
    class Meta:
        model = Budget
        fields = ['name', 'period_type', 'start_date', 'end_date', 'currency', 'status', 'notes']
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'e.g., Q1 2024 Operations'}),
            'period_type': forms.Select(attrs={'class': 'form-select'}),
            'start_date': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'end_date': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'currency': forms.Select(attrs={'class': 'form-select'}),
            'status': forms.Select(attrs={'class': 'form-select'}),
            'notes': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
        }


class BudgetItemForm(forms.ModelForm):
    class Meta:
        model = BudgetItem
        fields = ['category', 'description', 'amount']
        widgets = {
            'category': forms.Select(attrs={'class': 'form-select'}),
            'description': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'e.g., Plumbing repairs'}),
            'amount': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
        }


class ExpenseForm(forms.ModelForm):
    class Meta:
        model = Expense
        fields = [
            'budget_item', 'property_obj', 'rental', 'expense_type',
            'description', 'amount', 'currency', 'vendor_name',
            'invoice_number', 'expense_date', 'status', 'receipt_file', 'notes'
        ]
        widgets = {
            'budget_item': forms.Select(attrs={'class': 'form-select'}),
            'property_obj': forms.Select(attrs={'class': 'form-select'}),
            'rental': forms.Select(attrs={'class': 'form-select'}),
            'expense_type': forms.Select(attrs={'class': 'form-select'}),
            'description': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Description of expense'}),
            'amount': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'currency': forms.Select(attrs={'class': 'form-select'}),
            'vendor_name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Vendor/Supplier name'}),
            'invoice_number': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Vendor invoice number'}),
            'expense_date': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'status': forms.Select(attrs={'class': 'form-select'}),
            'receipt_file': forms.FileInput(attrs={'class': 'form-control'}),
            'notes': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Filter budget items to only active budgets
        self.fields['budget_item'].queryset = BudgetItem.objects.filter(budget__status='active').select_related('budget')
        self.fields['property_obj'].queryset = Property.objects.all()
        self.fields['rental'].queryset = Rental.objects.filter(status__in=['active', 'pending']).select_related('property_obj', 'tenant')
        # Make budget_item, property_obj, and rental optional
        self.fields['budget_item'].required = False
        self.fields['property_obj'].required = False
        self.fields['rental'].required = False
