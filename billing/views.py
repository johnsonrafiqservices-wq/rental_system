from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator
from django.db.models import Q, Sum
from django.utils import timezone
from datetime import date, timedelta
from .models import Invoice, Payment, Budget, BudgetItem, Expense
from .forms import InvoiceForm, PaymentForm, BudgetForm, BudgetItemForm, ExpenseForm
from .utils import generate_invoices_for_rental
from rentals.models import Owner, Property, Rental


@login_required
def billing_dashboard(request):
    """Billing overview dashboard"""
    today = date.today()

    total_invoices = Invoice.objects.count()
    total_revenue = Payment.objects.filter(status='completed').aggregate(total=Sum('amount'))['total'] or 0
    pending_amount = Invoice.objects.exclude(status__in=['paid', 'cancelled']).count()
    overdue_invoices = Invoice.objects.filter(
        due_date__lt=today
    ).exclude(status__in=['paid', 'cancelled']).count()

    # Revenue this month
    month_start = today.replace(day=1)
    monthly_revenue = Payment.objects.filter(
        status='completed',
        payment_date__gte=month_start
    ).aggregate(total=Sum('amount'))['total'] or 0

    recent_invoices = Invoice.objects.select_related('rental__property_obj', 'rental__tenant')[:5]
    recent_payments = Payment.objects.select_related('invoice__rental__property_obj')[:5]

    # Upcoming due invoices (next 7 days)
    upcoming_due = Invoice.objects.filter(
        due_date__gte=today,
        due_date__lte=today + timedelta(days=7)
    ).exclude(status__in=['paid', 'cancelled']).select_related('rental__property_obj', 'rental__tenant')[:5]

    context = {
        'total_invoices': total_invoices,
        'total_revenue': total_revenue,
        'pending_amount': pending_amount,
        'overdue_invoices': overdue_invoices,
        'monthly_revenue': monthly_revenue,
        'recent_invoices': recent_invoices,
        'recent_payments': recent_payments,
        'upcoming_due': upcoming_due,
    }
    return render(request, 'billing/billing_dashboard.html', context)


@login_required
def invoice_list(request):
    """List all invoices with filters"""
    invoices = Invoice.objects.select_related('rental__property_obj', 'rental__tenant')

    search = request.GET.get('search')
    status = request.GET.get('status')

    if search:
        invoices = invoices.filter(
            Q(invoice_number__icontains=search) |
            Q(rental__property_obj__name__icontains=search) |
            Q(rental__tenant__company_name__icontains=search) |
            Q(rental__tenant__first_name__icontains=search) |
            Q(rental__tenant__last_name__icontains=search)
        )
    if status:
        invoices = invoices.filter(status=status)

    paginator = Paginator(invoices, 20)
    page_obj = paginator.get_page(request.GET.get('page'))

    context = {
        'page_obj': page_obj,
        'search': search or '',
        'status': status or '',
    }
    return render(request, 'billing/invoice_list.html', context)


@login_required
def invoice_create(request):
    """Create a new invoice"""
    if request.method == 'POST':
        form = InvoiceForm(request.POST)
        if form.is_valid():
            invoice = form.save()
            messages.success(request, f'Invoice {invoice.invoice_number} created successfully.')
            return redirect('billing:invoice_detail', pk=invoice.pk)
    else:
        rental_id = request.GET.get('rental')
        form = InvoiceForm(rental_id=rental_id)
        if rental_id:
            try:
                rental = Rental.objects.get(pk=rental_id)
                form.fields['rent_amount'].initial = rental.monthly_rent
                form.fields['currency'].initial = rental.currency
            except Rental.DoesNotExist:
                pass

    return render(request, 'billing/invoice_form.html', {'form': form, 'title': 'Create Invoice'})


@login_required
def invoice_detail(request, pk):
    """View invoice details"""
    invoice = get_object_or_404(Invoice.objects.select_related('rental__property_obj', 'rental__tenant'), pk=pk)
    payments = invoice.payments.all()

    context = {'invoice': invoice, 'payments': payments}
    return render(request, 'billing/invoice_detail.html', context)


@login_required
def invoice_edit(request, pk):
    """Edit an existing invoice"""
    invoice = get_object_or_404(Invoice, pk=pk)
    if request.method == 'POST':
        form = InvoiceForm(request.POST, instance=invoice)
        if form.is_valid():
            form.save()
            messages.success(request, f'Invoice {invoice.invoice_number} updated.')
            return redirect('billing:invoice_detail', pk=invoice.pk)
    else:
        form = InvoiceForm(instance=invoice)

    return render(request, 'billing/invoice_form.html', {'form': form, 'title': 'Edit Invoice', 'invoice': invoice})


@login_required
def payment_list(request):
    """List all payments"""
    payments = Payment.objects.select_related('invoice__rental__property_obj', 'invoice__rental__tenant')

    search = request.GET.get('search')
    method = request.GET.get('method')

    if search:
        payments = payments.filter(
            Q(receipt_number__icontains=search) |
            Q(invoice__invoice_number__icontains=search) |
            Q(reference__icontains=search) |
            Q(invoice__rental__property_obj__name__icontains=search)
        )
    if method:
        payments = payments.filter(payment_method=method)

    paginator = Paginator(payments, 20)
    page_obj = paginator.get_page(request.GET.get('page'))

    context = {
        'page_obj': page_obj,
        'search': search or '',
        'method': method or '',
    }
    return render(request, 'billing/payment_list.html', context)


@login_required
def payment_create(request):
    """Record a new payment"""
    if request.method == 'POST':
        form = PaymentForm(request.POST)
        if form.is_valid():
            payment = form.save()
            messages.success(request, f'Payment {payment.receipt_number} recorded successfully.')
            return redirect('billing:payment_detail', pk=payment.pk)
    else:
        invoice_id = request.GET.get('invoice')
        form = PaymentForm(invoice_id=invoice_id)
        if invoice_id:
            try:
                invoice = Invoice.objects.get(pk=invoice_id)
                form.fields['amount'].initial = invoice.balance_due
                form.fields['currency'].initial = invoice.currency
            except Invoice.DoesNotExist:
                pass

    return render(request, 'billing/payment_form.html', {'form': form, 'title': 'Record Payment'})


@login_required
def payment_detail(request, pk):
    """View payment details"""
    payment = get_object_or_404(Payment.objects.select_related('invoice__rental__property_obj', 'invoice__rental__tenant'), pk=pk)

    context = {'payment': payment}
    return render(request, 'billing/payment_detail.html', context)


@login_required
def invoice_print(request, pk):
    """Print view for invoice - professional formatted page"""
    invoice = get_object_or_404(Invoice.objects.select_related('rental__property_obj', 'rental__tenant', 'rental__property_obj__owner'), pk=pk)
    context = {'invoice': invoice}
    return render(request, 'billing/invoice_print.html', context)


@login_required
def receipt_print(request, pk):
    """Print view for receipt - professional formatted page"""
    payment = get_object_or_404(Payment.objects.select_related('invoice__rental__property_obj', 'invoice__rental__tenant', 'invoice__rental__property_obj__owner'), pk=pk)
    context = {'payment': payment}
    return render(request, 'billing/receipt_print.html', context)


@login_required
def generate_rental_invoices(request, rental_pk):
    """Generate missing invoices for a rental based on its payment schedule."""
    rental = get_object_or_404(Rental, pk=rental_pk)
    created = generate_invoices_for_rental(rental)
    if created:
        messages.success(request, f'{len(created)} invoice(s) generated for {rental.rental_number}.')
    else:
        messages.info(request, 'All invoices are already up to date — nothing new to generate.')
    return redirect('rentals:rental_detail', pk=rental_pk)


@login_required
def record_rental_payment(request, rental_pk):
    """
    Record a payment directly from the rental detail page.
    Expects POST with: invoice_id (or 'auto'), amount, currency,
    payment_method, payment_date, reference, notes.
    If invoice_id == 'auto', auto-generates or picks the oldest unpaid invoice.
    """
    rental = get_object_or_404(Rental, pk=rental_pk)

    if request.method == 'POST':
        invoice_id = request.POST.get('invoice_id')

        # Resolve invoice
        if invoice_id == 'auto' or not invoice_id:
            # Try oldest unpaid; if none, generate then pick
            invoice = (
                Invoice.objects.filter(rental=rental)
                .exclude(status__in=['paid', 'cancelled'])
                .order_by('period_start')
                .first()
            )
            if not invoice:
                generated = generate_invoices_for_rental(rental)
                invoice = generated[0] if generated else None
            if not invoice:
                messages.error(request, 'No open invoices found and no periods to generate. Check the rental start date.')
                return redirect('rentals:rental_detail', pk=rental_pk)
        else:
            invoice = get_object_or_404(Invoice, pk=invoice_id, rental=rental)

        try:
            amount = float(request.POST.get('amount', 0))
            if amount <= 0:
                raise ValueError
        except (ValueError, TypeError):
            messages.error(request, 'Invalid payment amount.')
            return redirect('rentals:rental_detail', pk=rental_pk)

        payment = Payment.objects.create(
            invoice=invoice,
            amount=amount,
            currency=request.POST.get('currency', rental.currency),
            payment_method=request.POST.get('payment_method', 'cash'),
            status='completed',
            payment_date=request.POST.get('payment_date') or date.today(),
            reference=request.POST.get('reference', '') or None,
            notes=request.POST.get('notes', '') or None,
        )
        messages.success(request, f'Payment {payment.receipt_number} recorded against {invoice.invoice_number}.')
        return redirect('rentals:rental_detail', pk=rental_pk)

    return redirect('rentals:rental_detail', pk=rental_pk)


# ──────────────────────────────────────────────
# Budget Management
# ──────────────────────────────────────────────

@login_required
def budget_list(request):
    """List all budgets"""
    budgets = Budget.objects.prefetch_related('items').all()
    return render(request, 'billing/budget_list.html', {'budgets': budgets})


@login_required
def budget_create(request):
    """Create a new budget"""
    if request.method == 'POST':
        form = BudgetForm(request.POST)
        if form.is_valid():
            budget = form.save()
            messages.success(request, f'Budget "{budget.name}" created successfully.')
            return redirect('billing:budget_detail', pk=budget.pk)
    else:
        form = BudgetForm()
    return render(request, 'billing/budget_form.html', {'form': form, 'title': 'Create Budget'})


@login_required
def budget_detail(request, pk):
    """View budget details with items"""
    budget = get_object_or_404(Budget, pk=pk)
    items = budget.items.prefetch_related('expenses')
    return render(request, 'billing/budget_detail.html', {'budget': budget, 'items': items})


@login_required
def budget_edit(request, pk):
    """Edit a budget"""
    budget = get_object_or_404(Budget, pk=pk)
    if request.method == 'POST':
        form = BudgetForm(request.POST, instance=budget)
        if form.is_valid():
            form.save()
            messages.success(request, 'Budget updated successfully.')
            return redirect('billing:budget_detail', pk=budget.pk)
    else:
        form = BudgetForm(instance=budget)
    return render(request, 'billing/budget_form.html', {'form': form, 'budget': budget, 'title': 'Edit Budget'})


@login_required
def budget_delete(request, pk):
    """Delete a budget"""
    budget = get_object_or_404(Budget, pk=pk)
    if request.method == 'POST':
        budget.delete()
        messages.success(request, 'Budget deleted successfully.')
        return redirect('billing:budget_list')
    return render(request, 'billing/budget_confirm_delete.html', {'budget': budget})


@login_required
def budget_item_create(request, budget_pk):
    """Add a budget item to a budget"""
    budget = get_object_or_404(Budget, pk=budget_pk)
    if request.method == 'POST':
        form = BudgetItemForm(request.POST)
        if form.is_valid():
            item = form.save(commit=False)
            item.budget = budget
            item.save()
            messages.success(request, 'Budget item added successfully.')
            return redirect('billing:budget_detail', pk=budget.pk)
    else:
        form = BudgetItemForm()
    return render(request, 'billing/budget_item_form.html', {'form': form, 'budget': budget})


@login_required
def budget_item_delete(request, pk):
    """Delete a budget item"""
    item = get_object_or_404(BudgetItem, pk=pk)
    budget_pk = item.budget.pk
    if request.method == 'POST':
        item.delete()
        messages.success(request, 'Budget item deleted successfully.')
        return redirect('billing:budget_detail', pk=budget_pk)
    return render(request, 'billing/budget_item_confirm_delete.html', {'item': item})


# ──────────────────────────────────────────────
# Expense Management
# ──────────────────────────────────────────────

@login_required
def expense_list(request):
    """List all expenses with filtering"""
    expenses = Expense.objects.select_related('budget_item__budget', 'property_obj', 'rental').all()

    # Filters
    status = request.GET.get('status')
    category = request.GET.get('category')
    date_from = request.GET.get('date_from')
    date_to = request.GET.get('date_to')

    if status:
        expenses = expenses.filter(status=status)
    if category:
        expenses = expenses.filter(budget_item__category=category)
    if date_from:
        expenses = expenses.filter(expense_date__gte=date_from)
    if date_to:
        expenses = expenses.filter(expense_date__lte=date_to)

    paginator = Paginator(expenses, 25)
    page = request.GET.get('page')
    page_obj = paginator.get_page(page)

    context = {
        'page_obj': page_obj,
        'status': status,
        'category': category,
        'date_from': date_from,
        'date_to': date_to,
    }
    return render(request, 'billing/expense_list.html', context)


@login_required
def expense_create(request):
    """Create a new expense"""
    if request.method == 'POST':
        form = ExpenseForm(request.POST, request.FILES)
        if form.is_valid():
            expense = form.save()
            messages.success(request, f'Expense {expense.expense_number} created successfully.')
            return redirect('billing:expense_detail', pk=expense.pk)
    else:
        form = ExpenseForm()
    return render(request, 'billing/expense_form.html', {'form': form, 'title': 'Create Expense'})


@login_required
def expense_detail(request, pk):
    """View expense details"""
    expense = get_object_or_404(Expense, pk=pk)
    return render(request, 'billing/expense_detail.html', {'expense': expense})


@login_required
def expense_edit(request, pk):
    """Edit an expense"""
    expense = get_object_or_404(Expense, pk=pk)
    if request.method == 'POST':
        form = ExpenseForm(request.POST, request.FILES, instance=expense)
        if form.is_valid():
            form.save()
            messages.success(request, 'Expense updated successfully.')
            return redirect('billing:expense_detail', pk=expense.pk)
    else:
        form = ExpenseForm(instance=expense)
    return render(request, 'billing/expense_form.html', {'form': form, 'expense': expense, 'title': 'Edit Expense'})


@login_required
def expense_delete(request, pk):
    """Delete an expense"""
    expense = get_object_or_404(Expense, pk=pk)
    if request.method == 'POST':
        expense.delete()
        messages.success(request, 'Expense deleted successfully.')
        return redirect('billing:expense_list')
    return render(request, 'billing/expense_confirm_delete.html', {'expense': expense})


# ──────────────────────────────────────────────
# Financial Reports
# ──────────────────────────────────────────────

@login_required
def financial_report(request):
    """
    Comprehensive financial report showing:
    - Income vs Expenses
    - Budget utilization
    - Projections
    - Property performance
    """
    from_date = request.GET.get('from_date')
    to_date = request.GET.get('to_date')
    property_id = request.GET.get('property')
    owner_id = request.GET.get('owner')
    rental_id = request.GET.get('rental')

    today = date.today()
    if not from_date:
        from_date = today.replace(day=1).strftime('%Y-%m-%d')
    if not to_date:
        to_date = today.strftime('%Y-%m-%d')

    selected_property = property_id or ''
    selected_owner = owner_id or ''
    selected_rental = rental_id or ''

    # Filter options
    properties = Property.objects.select_related('owner').order_by('name')
    owners = Owner.objects.order_by('company_name', 'first_name', 'last_name')
    rentals = Rental.objects.select_related('property_obj').order_by('-created_at')

    # Income (Payments received)
    payment_filters = Q(
        status='completed',
        payment_date__gte=from_date,
        payment_date__lte=to_date
    )
    if selected_property:
        payment_filters &= Q(invoice__rental__property_obj_id=selected_property)
    if selected_owner:
        payment_filters &= Q(invoice__rental__property_obj__owner_id=selected_owner)
    if selected_rental:
        payment_filters &= Q(invoice__rental_id=selected_rental)

    income = Payment.objects.filter(payment_filters).aggregate(total=Sum('amount'))['total'] or 0

    # Expenses
    expense_filters = Q(
        status__in=['approved', 'paid'],
        expense_date__gte=from_date,
        expense_date__lte=to_date
    )
    if selected_property:
        expense_filters &= (Q(property_obj_id=selected_property) | Q(rental__property_obj_id=selected_property))
    if selected_owner:
        expense_filters &= (Q(property_obj__owner_id=selected_owner) | Q(rental__property_obj__owner_id=selected_owner))
    if selected_rental:
        expense_filters &= Q(rental_id=selected_rental)

    expenses = Expense.objects.filter(expense_filters).aggregate(total=Sum('amount'))['total'] or 0

    # Net income
    net_income = income - expenses

    # Pending income (invoices not yet paid)
    invoice_filters = Q(
        status__in=['sent', 'partially_paid'],
        issue_date__gte=from_date,
        issue_date__lte=to_date
    )
    if selected_property:
        invoice_filters &= Q(rental__property_obj_id=selected_property)
    if selected_owner:
        invoice_filters &= Q(rental__property_obj__owner_id=selected_owner)
    if selected_rental:
        invoice_filters &= Q(rental_id=selected_rental)

    pending_invoices = Invoice.objects.filter(invoice_filters).prefetch_related('payments')
    pending_income = sum(inv.balance_due for inv in pending_invoices) or 0

    # Budget utilization
    active_budgets = Budget.objects.filter(status='active')
    total_budgeted = sum(b.total_budgeted for b in active_budgets)
    total_spent = sum(b.total_spent for b in active_budgets)
    budget_remaining = total_budgeted - total_spent

    # Expenses by category
    expenses_by_category = Expense.objects.filter(expense_filters).values('budget_item__category').annotate(
        total=Sum('amount')
    ).order_by('-total')

    # Monthly trend (last 6 months)
    months = []
    income_trend = []
    expense_trend = []

    for i in range(5, -1, -1):
        month_date = today.replace(day=1) - timedelta(days=i*30)
        month_start = month_date.replace(day=1)
        if month_date.month == 12:
            month_end = month_date.replace(day=31)
        else:
            month_end = (month_start.replace(month=month_start.month+1, day=1)) - timedelta(days=1)

        month_income = Payment.objects.filter(
            status='completed',
            payment_date__gte=month_start,
            payment_date__lte=month_end
            ).filter(
                Q() if not selected_property else Q(invoice__rental__property_obj_id=selected_property),
                Q() if not selected_owner else Q(invoice__rental__property_obj__owner_id=selected_owner),
                Q() if not selected_rental else Q(invoice__rental_id=selected_rental),
        ).aggregate(total=Sum('amount'))['total'] or 0

        month_expense = Expense.objects.filter(
            status__in=['approved', 'paid'],
            expense_date__gte=month_start,
            expense_date__lte=month_end
            ).filter(
                Q() if not selected_property else (Q(property_obj_id=selected_property) | Q(rental__property_obj_id=selected_property)),
                Q() if not selected_owner else (Q(property_obj__owner_id=selected_owner) | Q(rental__property_obj__owner_id=selected_owner)),
                Q() if not selected_rental else Q(rental_id=selected_rental),
        ).aggregate(total=Sum('amount'))['total'] or 0

        months.append(month_date.strftime('%b %Y'))
        income_trend.append(float(month_income))
        expense_trend.append(float(month_expense))

    # Property performance
    property_performance = []
    property_queryset = Property.objects.all()
    if selected_property:
        property_queryset = property_queryset.filter(pk=selected_property)
    if selected_owner:
        property_queryset = property_queryset.filter(owner_id=selected_owner)
    if selected_rental:
        property_queryset = property_queryset.filter(rentals__id=selected_rental)

    for prop in property_queryset.distinct():
        prop_income = Payment.objects.filter(
            status='completed',
            invoice__rental__property_obj=prop,
            payment_date__gte=from_date,
            payment_date__lte=to_date
        ).aggregate(total=Sum('amount'))['total'] or 0

        prop_expense = Expense.objects.filter(
            status__in=['approved', 'paid'],
            property_obj=prop,
            expense_date__gte=from_date,
            expense_date__lte=to_date
        ).aggregate(total=Sum('amount'))['total'] or 0

        if prop_income > 0 or prop_expense > 0:
            property_performance.append({
                'property': prop,
                'income': prop_income,
                'expenses': prop_expense,
                'net': prop_income - prop_expense
            })

    # Projections
    avg_monthly_income = sum(income_trend) / len(income_trend) if income_trend else 0
    avg_monthly_expense = sum(expense_trend) / len(expense_trend) if expense_trend else 0

    projection_3_month = (avg_monthly_income - avg_monthly_expense) * 3
    projection_6_month = (avg_monthly_income - avg_monthly_expense) * 6
    projection_12_month = (avg_monthly_income - avg_monthly_expense) * 12

    context = {
        'from_date': from_date,
        'to_date': to_date,
        'selected_property': selected_property,
        'selected_owner': selected_owner,
        'selected_rental': selected_rental,
        'properties': properties,
        'owners': owners,
        'rentals': rentals,
        'income': income,
        'expenses': expenses,
        'net_income': net_income,
        'pending_income': pending_income,
        'total_budgeted': total_budgeted,
        'total_spent': total_spent,
        'budget_remaining': budget_remaining,
        'budget_utilization': round((total_spent / total_budgeted * 100), 1) if total_budgeted else 0,
        'expenses_by_category': expenses_by_category,
        'months': months,
        'income_trend': income_trend,
        'expense_trend': expense_trend,
        'property_performance': property_performance,
        'avg_monthly_income': avg_monthly_income,
        'avg_monthly_expense': avg_monthly_expense,
        'projection_3_month': projection_3_month,
        'projection_6_month': projection_6_month,
        'projection_12_month': projection_12_month,
    }
    return render(request, 'billing/financial_report.html', context)
