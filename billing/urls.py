from django.urls import path
from . import views

app_name = 'billing'

urlpatterns = [
    path('', views.billing_dashboard, name='billing_dashboard'),

    # Invoices
    path('invoices/', views.invoice_list, name='invoice_list'),
    path('invoices/create/', views.invoice_create, name='invoice_create'),
    path('invoices/<uuid:pk>/', views.invoice_detail, name='invoice_detail'),
    path('invoices/<uuid:pk>/edit/', views.invoice_edit, name='invoice_edit'),
    path('invoices/<uuid:pk>/print/', views.invoice_print, name='invoice_print'),

    # Payments
    path('payments/', views.payment_list, name='payment_list'),
    path('payments/create/', views.payment_create, name='payment_create'),
    path('payments/<uuid:pk>/', views.payment_detail, name='payment_detail'),
    path('payments/<uuid:pk>/print/', views.receipt_print, name='receipt_print'),

    # Budgets
    path('budgets/', views.budget_list, name='budget_list'),
    path('budgets/create/', views.budget_create, name='budget_create'),
    path('budgets/<uuid:pk>/', views.budget_detail, name='budget_detail'),
    path('budgets/<uuid:pk>/edit/', views.budget_edit, name='budget_edit'),
    path('budgets/<uuid:pk>/delete/', views.budget_delete, name='budget_delete'),
    path('budgets/<uuid:budget_pk>/items/create/', views.budget_item_create, name='budget_item_create'),
    path('budget-items/<uuid:pk>/delete/', views.budget_item_delete, name='budget_item_delete'),

    # Expenses
    path('expenses/', views.expense_list, name='expense_list'),
    path('expenses/create/', views.expense_create, name='expense_create'),
    path('expenses/<uuid:pk>/', views.expense_detail, name='expense_detail'),
    path('expenses/<uuid:pk>/edit/', views.expense_edit, name='expense_edit'),
    path('expenses/<uuid:pk>/delete/', views.expense_delete, name='expense_delete'),

    # Financial Reports
    path('reports/', views.financial_report, name='financial_report'),

    # Rental-scoped shortcuts
    path('rentals/<uuid:rental_pk>/generate-invoices/', views.generate_rental_invoices, name='generate_rental_invoices'),
    path('rentals/<uuid:rental_pk>/record-payment/', views.record_rental_payment, name='record_rental_payment'),
]
