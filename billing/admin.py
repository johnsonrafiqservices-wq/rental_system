from django.contrib import admin
from .models import Invoice, Payment


@admin.register(Invoice)
class InvoiceAdmin(admin.ModelAdmin):
    list_display = ('invoice_number', 'rental', 'status', 'total_amount', 'amount_paid', 'balance_due', 'due_date')
    list_filter = ('status', 'currency')
    search_fields = ('invoice_number', 'rental__property_obj__name', 'rental__tenant__company_name')
    readonly_fields = ('invoice_number', 'created_at', 'updated_at')


@admin.register(Payment)
class PaymentAdmin(admin.ModelAdmin):
    list_display = ('receipt_number', 'invoice', 'amount', 'payment_method', 'status', 'payment_date')
    list_filter = ('status', 'payment_method')
    search_fields = ('receipt_number', 'reference', 'invoice__invoice_number')
    readonly_fields = ('receipt_number', 'created_at', 'updated_at')
