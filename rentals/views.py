from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.core.paginator import Paginator
from django.db.models import Count, Q, Sum
from django.utils import timezone
from datetime import timedelta
from .models import Owner, Tenant, Property, QRCode, Rental, RentalAgreement
from .forms import OwnerForm, TenantForm, PropertyForm, RentalForm


def login_view(request):
    """Email + password login"""
    if request.user.is_authenticated:
        return redirect('rentals:dashboard')
    error = None
    email = ''
    if request.method == 'POST':
        email = request.POST.get('email', '').strip()
        password = request.POST.get('password', '')
        next_url = request.POST.get('next', '/')
        user = authenticate(request, username=email, password=password)
        if user is not None:
            login(request, user)
            return redirect(next_url or 'rentals:dashboard')
        error = 'Invalid email or password. Please try again.'
    else:
        next_url = request.GET.get('next', '')
    return render(request, 'rentals/login.html', {'error': error, 'email': email, 'next': next_url})


def logout_view(request):
    """Log out and redirect to login"""
    logout(request)
    return redirect('rentals:login')


@login_required
def dashboard(request):
    """Main dashboard showing overview of rentals"""
    from django.utils import timezone
    from datetime import timedelta
    
    total_owners = Owner.objects.count()
    total_tenants = Tenant.objects.count()
    total_properties = Property.objects.filter(is_active=True).count()
    total_rentals = Rental.objects.count()
    
    # Currently active rentals (where today is between start_date and end_date)
    today = timezone.now().date()
    currently_active_rentals = Rental.objects.filter(
        status='active',
        start_date__lte=today,
        end_date__gte=today
    ).count()
    
    available_properties = Property.objects.filter(is_active=True, is_available=True).count()
    
    # Total rentable units (sum of all number_of_units)
    total_rentable_units = Property.objects.filter(is_active=True).aggregate(
        total=Sum('number_of_units')
    )['total'] or 0
    
    # Expiring leases (next 30 days)
    thirty_days_from_now = today + timedelta(days=30)
    expiring_leases = Rental.objects.filter(
        status='active',
        end_date__gte=today,
        end_date__lte=thirty_days_from_now
    ).order_by('end_date')[:5]
    
    recent_properties = Property.objects.filter(is_active=True).order_by('-created_at')[:5]
    recent_rentals = Rental.objects.all().order_by('-created_at')[:5]
    
    context = {
        'total_owners': total_owners,
        'total_tenants': total_tenants,
        'total_properties': total_properties,
        'total_rentals': total_rentals,
        'active_rentals': currently_active_rentals,
        'available_properties': available_properties,
        'total_rentable_units': total_rentable_units,
        'expiring_leases': expiring_leases,
        'recent_properties': recent_properties,
        'recent_rentals': recent_rentals,
    }
    return render(request, 'rentals/dashboard.html', context)


@login_required
def owner_list(request):
    """List all owners (companies and individuals)"""
    owners = Owner.objects.all()
    
    search = request.GET.get('search')
    owner_type = request.GET.get('owner_type')
    
    if search:
        owners = owners.filter(
            Q(company_name__icontains=search) |
            Q(first_name__icontains=search) |
            Q(last_name__icontains=search) |
            Q(email__icontains=search)
        )
    
    if owner_type:
        owners = owners.filter(owner_type=owner_type)
    
    paginator = Paginator(owners, 20)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    context = {
        'page_obj': page_obj,
        'search': search or '',
        'owner_type': owner_type or '',
    }
    return render(request, 'rentals/owner_list.html', context)


@login_required
def owner_create(request):
    """Register a new owner (company or individual)"""
    if request.method == 'POST':
        form = OwnerForm(request.POST)
        if form.is_valid():
            owner = form.save()
            messages.success(request, f'{owner.name} has been registered successfully.')
            return redirect('rentals:owner_detail', pk=owner.pk)
    else:
        form = OwnerForm()
    
    context = {'form': form}
    return render(request, 'rentals/owner_form.html', context)


@login_required
def owner_detail(request, pk):
    """View owner details with their properties"""
    from billing.models import Payment
    owner = get_object_or_404(Owner, pk=pk)
    properties = owner.properties.filter(is_active=True)
    
    # Rentals on properties owned by this owner
    property_rentals = Rental.objects.filter(
        property_obj__owner=owner
    ).select_related('property_obj', 'tenant').order_by('-created_at')
    
    # Payment history for rentals on owner's properties
    payments = Payment.objects.filter(
        invoice__rental__property_obj__owner=owner
    ).select_related('invoice__rental__property_obj', 'invoice__rental__tenant').order_by('-payment_date')
    
    context = {
        'owner': owner,
        'properties': properties,
        'property_rentals': property_rentals,
        'payments': payments,
    }
    return render(request, 'rentals/owner_detail.html', context)


@login_required
def tenant_list(request):
    """List all tenants"""
    tenants = Tenant.objects.all()
    
    search = request.GET.get('search')
    tenant_type = request.GET.get('tenant_type')
    
    if search:
        tenants = tenants.filter(
            Q(company_name__icontains=search) |
            Q(first_name__icontains=search) |
            Q(last_name__icontains=search) |
            Q(email__icontains=search)
        )
    
    if tenant_type:
        tenants = tenants.filter(tenant_type=tenant_type)
    
    paginator = Paginator(tenants, 20)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    context = {
        'page_obj': page_obj,
        'search': search or '',
        'tenant_type': tenant_type or '',
    }
    return render(request, 'rentals/tenant_list.html', context)


@login_required
def tenant_create(request):
    """Tenants can only be created from a rental detail page."""
    messages.warning(request, 'Tenants can only be added from a rental detail page.')
    return redirect('rentals:rental_list')


@login_required
def tenant_detail(request, pk):
    """View tenant details with their rentals"""
    from billing.models import Payment
    tenant = get_object_or_404(Tenant, pk=pk)
    tenant_rentals = tenant.rentals.all().select_related('property_obj').order_by('-created_at')
    
    # Payment history for this tenant's rentals
    payments = Payment.objects.filter(
        invoice__rental__tenant=tenant
    ).select_related('invoice__rental__property_obj').order_by('-payment_date')
    
    context = {
        'tenant': tenant,
        'tenant_rentals': tenant_rentals,
        'payments': payments,
    }
    return render(request, 'rentals/tenant_detail.html', context)


@login_required
def property_list(request):
    """List all properties"""
    properties = Property.objects.filter(is_active=True).select_related('owner')
    
    search = request.GET.get('search')
    property_type = request.GET.get('property_type')
    city = request.GET.get('city')
    available_only = request.GET.get('available_only')
    
    if search:
        properties = properties.filter(
            Q(name__icontains=search) |
            Q(address__icontains=search) |
            Q(owner__company_name__icontains=search) |
            Q(owner__first_name__icontains=search)
        )
    
    if property_type:
        properties = properties.filter(property_type=property_type)
    
    if city:
        properties = properties.filter(city__icontains=city)
    
    if available_only:
        properties = properties.filter(is_available=True)
    
    paginator = Paginator(properties, 20)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    context = {
        'page_obj': page_obj,
        'search': search or '',
        'property_type': property_type or '',
        'city': city or '',
        'available_only': available_only,
    }
    return render(request, 'rentals/property_list.html', context)


@login_required
def property_create(request):
    """Create a new property"""
    if request.method == 'POST':
        form = PropertyForm(request.POST)
        if form.is_valid():
            property_obj = form.save()
            # Auto-generate QR code for the property
            QRCode.objects.create(property_obj=property_obj)
            messages.success(request, f'{property_obj.name} has been created with QR code.')
            return redirect('rentals:property_detail', pk=property_obj.pk)
    else:
        form = PropertyForm()
    
    context = {'form': form}
    return render(request, 'rentals/property_form.html', context)


@login_required
def property_detail(request, pk):
    """View property details"""
    property_obj = get_object_or_404(Property, pk=pk)
    rentals = property_obj.rentals.all().order_by('-created_at')
    all_tenants = Tenant.objects.all()
    
    context = {'property': property_obj, 'rentals': rentals, 'all_tenants': all_tenants}
    return render(request, 'rentals/property_detail.html', context)


@login_required
def rental_list(request):
    """List all rentals"""
    rentals = Rental.objects.all().select_related('property_obj', 'tenant')
    
    status = request.GET.get('status')
    search = request.GET.get('search')
    
    if status:
        rentals = rentals.filter(status=status)
    
    if search:
        rentals = rentals.filter(
            Q(property_obj__name__icontains=search) |
            Q(tenant__first_name__icontains=search) |
            Q(tenant__last_name__icontains=search) |
            Q(tenant__company_name__icontains=search)
        )
    
    paginator = Paginator(rentals, 20)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    context = {
        'page_obj': page_obj,
        'status': status or '',
        'search': search or '',
    }
    return render(request, 'rentals/rental_list.html', context)


@login_required
def rental_create(request):
    """Register a new rental attached to a property (tenant added later from detail page)"""
    if request.method == 'POST':
        form = RentalForm(request.POST)
        if form.is_valid():
            rental = form.save()
            if rental.status == 'active':
                rental.property_obj.is_available = False
                rental.property_obj.save()
            messages.success(request, f'Rental for {rental.property_obj.name} has been registered.')
            return redirect('rentals:rental_detail', pk=rental.pk)
    else:
        form = RentalForm()
        property_id = request.GET.get('property')
        if property_id:
            try:
                form.fields['property_obj'].initial = Property.objects.get(pk=property_id)
            except Property.DoesNotExist:
                pass
    
    context = {'form': form}
    return render(request, 'rentals/rental_form.html', context)


@login_required
def rental_detail(request, pk):
    """View rental details"""
    rental = get_object_or_404(Rental.objects.select_related('property_obj', 'property_obj__owner', 'tenant'), pk=pk)
    
    # Other rentals for the same property (excluding this one)
    rental_history = Rental.objects.filter(
        property_obj=rental.property_obj
    ).exclude(pk=rental.pk).select_related('tenant').order_by('-created_at')

    # Past tenants: tenants from expired/terminated rentals on the same property
    past_tenants = (
        Rental.objects
        .filter(property_obj=rental.property_obj, status__in=['expired', 'terminated'])
        .exclude(tenant__isnull=True)
        .select_related('tenant')
        .order_by('-end_date', '-updated_at')
    )

    # Get all tenants for the assign existing tenant modal
    all_tenants = Tenant.objects.all().order_by('first_name', 'last_name', 'company_name')

    # Billing data
    from billing.models import Invoice, Payment as BillingPayment
    invoices = Invoice.objects.filter(rental=rental).order_by('-period_start')
    open_invoices = invoices.exclude(status__in=['paid', 'cancelled'])
    payments = BillingPayment.objects.filter(invoice__rental=rental).select_related('invoice').order_by('-payment_date')

    context = {
        'rental': rental,
        'rental_history': rental_history,
        'past_tenants': past_tenants,
        'all_tenants': all_tenants,
        'invoices': invoices,
        'open_invoices': open_invoices,
        'payments': payments,
    }
    return render(request, 'rentals/rental_detail.html', context)


@login_required
def rental_edit(request, pk):
    """Edit an existing rental's information"""
    rental = get_object_or_404(Rental, pk=pk)
    if request.method == 'POST':
        form = RentalForm(request.POST, instance=rental)
        if form.is_valid():
            rental = form.save()
            messages.success(request, f'Rental {rental.rental_number} updated successfully.')
            return redirect('rentals:rental_detail', pk=rental.pk)
    else:
        form = RentalForm(instance=rental)
    context = {'form': form, 'rental': rental, 'editing': True}
    return render(request, 'rentals/rental_form.html', context)


@login_required
def add_tenant_to_rental(request, pk):
    """Add a tenant to an existing rental"""
    rental = get_object_or_404(Rental, pk=pk)
    
    if rental.tenant:
        messages.error(request, 'This rental already has a tenant assigned.')
        return redirect('rentals:rental_detail', pk=rental.pk)
    
    if request.method == 'POST':
        # Check if assigning existing tenant or creating new one
        tenant_id = request.POST.get('tenant')
        tenant_type = request.POST.get('tenant_type')
        
        if tenant_id:
            # Assign existing tenant
            try:
                tenant = Tenant.objects.get(pk=tenant_id)
                rental.tenant = tenant
                rental.save()
                messages.success(request, f'{tenant.name} has been assigned to this rental.')
            except Tenant.DoesNotExist:
                messages.error(request, 'Selected tenant not found.')
        elif tenant_type:
            # Create new tenant
            tenant_data = {'tenant_type': tenant_type}
            
            if tenant_type == 'company':
                tenant_data['company_name'] = request.POST.get('company_name')
                tenant_data['registration_number'] = request.POST.get('registration_number')
                tenant_data['tax_id'] = request.POST.get('tax_id')
            else:
                tenant_data['first_name'] = request.POST.get('first_name')
                tenant_data['last_name'] = request.POST.get('last_name')
                tenant_data['national_id'] = request.POST.get('national_id')
            
            tenant_data['email'] = request.POST.get('email')
            tenant_data['phone'] = request.POST.get('phone')
            tenant_data['address'] = request.POST.get('address')
            tenant_data['city'] = request.POST.get('city')
            tenant_data['country'] = request.POST.get('country', 'Uganda')
            
            # Create the new tenant
            new_tenant = Tenant.objects.create(**tenant_data)
            rental.tenant = new_tenant
            rental.save()
            messages.success(request, f'{new_tenant.name} has been registered and assigned to this rental.')
        else:
            messages.error(request, 'Please select a tenant or register a new one.')
    
    return redirect('rentals:rental_detail', pk=rental.pk)


# JSON API Endpoints
@login_required
def api_owners(request):
    """JSON API for owners"""
    owners = Owner.objects.all()
    data = []
    for owner in owners:
        data.append({
            'id': str(owner.pk),
            'name': owner.name,
            'owner_type': owner.owner_type,
            'email': owner.email,
            'phone': owner.phone,
            'city': owner.city,
            'property_count': owner.property_count,
            'qr_code_url': owner.qr_code_image.url if owner.qr_code_image else None,
            'url': owner.get_absolute_url(),
        })
    return JsonResponse({'owners': data})


@login_required
def api_owner_detail(request, pk):
    """JSON API for single owner"""
    owner = get_object_or_404(Owner, pk=pk)
    data = {
        'id': str(owner.pk),
        'name': owner.name,
        'owner_type': owner.owner_type,
        'company_name': owner.company_name,
        'first_name': owner.first_name,
        'last_name': owner.last_name,
        'email': owner.email,
        'phone': owner.phone,
        'address': owner.address,
        'city': owner.city,
        'country': owner.country,
        'property_count': owner.property_count,
        'qr_code_url': owner.qr_code_image.url if owner.qr_code_image else None,
        'url': owner.get_absolute_url(),
    }
    return JsonResponse(data)


@login_required
def api_tenants(request):
    """JSON API for tenants"""
    tenants = Tenant.objects.all()
    data = []
    for tenant in tenants:
        data.append({
            'id': str(tenant.pk),
            'name': tenant.name,
            'tenant_type': tenant.tenant_type,
            'email': tenant.email,
            'phone': tenant.phone,
            'city': tenant.city,
            'rental_count': tenant.rental_count,
            'qr_code_url': tenant.qr_code_image.url if tenant.qr_code_image else None,
            'url': tenant.get_absolute_url(),
        })
    return JsonResponse({'tenants': data})


@login_required
def api_tenant_detail(request, pk):
    """JSON API for single tenant"""
    tenant = get_object_or_404(Tenant, pk=pk)
    data = {
        'id': str(tenant.pk),
        'name': tenant.name,
        'tenant_type': tenant.tenant_type,
        'company_name': tenant.company_name,
        'first_name': tenant.first_name,
        'last_name': tenant.last_name,
        'email': tenant.email,
        'phone': tenant.phone,
        'address': tenant.address,
        'city': tenant.city,
        'country': tenant.country,
        'rental_count': tenant.rental_count,
        'qr_code_url': tenant.qr_code_image.url if tenant.qr_code_image else None,
        'url': tenant.get_absolute_url(),
    }
    return JsonResponse(data)


@login_required
def api_properties(request):
    """JSON API for properties"""
    properties = Property.objects.filter(is_active=True).select_related('owner')
    data = []
    for prop in properties:
        data.append({
            'id': str(prop.pk),
            'name': prop.name,
            'property_type': prop.property_type,
            'address': prop.address,
            'city': prop.city,
            'owner': prop.owner.name,
            'owner_id': str(prop.owner.pk),
            'base_rent': str(prop.base_rent),
            'currency': prop.currency,
            'is_available': prop.is_available,
            'number_of_units': prop.number_of_units,
            'qr_code_url': prop.qr_code_image.url if prop.qr_code_image else None,
            'url': prop.get_absolute_url(),
        })
    return JsonResponse({'properties': data})


@login_required
def api_property_detail(request, pk):
    """JSON API for single property"""
    property_obj = get_object_or_404(Property, pk=pk)
    data = {
        'id': str(property_obj.pk),
        'name': property_obj.name,
        'property_type': property_obj.property_type,
        'description': property_obj.description,
        'address': property_obj.address,
        'city': property_obj.city,
        'state_province': property_obj.state_province,
        'postal_code': property_obj.postal_code,
        'country': property_obj.country,
        'latitude': str(property_obj.latitude) if property_obj.latitude else None,
        'longitude': str(property_obj.longitude) if property_obj.longitude else None,
        'area_sq_meters': str(property_obj.area_sq_meters),
        'number_of_rooms': property_obj.number_of_rooms,
        'number_of_bathrooms': property_obj.number_of_bathrooms,
        'number_of_units': property_obj.number_of_units,
        'base_rent': str(property_obj.base_rent),
        'currency': property_obj.currency,
        'is_active': property_obj.is_active,
        'is_available': property_obj.is_available,
        'owner': property_obj.owner.name,
        'owner_id': str(property_obj.owner.pk),
        'qr_code_url': property_obj.qr_code_image.url if property_obj.qr_code_image else None,
        'url': property_obj.get_absolute_url(),
    }
    return JsonResponse(data)


@login_required
def api_rentals(request):
    """JSON API for rentals"""
    rentals = Rental.objects.all().select_related('property_obj', 'tenant')
    data = []
    for rental in rentals:
        data.append({
            'id': str(rental.pk),
            'property': rental.property_obj.name,
            'property_id': str(rental.property_obj.pk),
            'tenant': rental.tenant.name if rental.tenant else None,
            'tenant_id': str(rental.tenant.pk) if rental.tenant else None,
            'status': rental.status,
            'calculated_status': rental.get_rental_status(),
            'start_date': rental.start_date.isoformat(),
            'end_date': rental.end_date.isoformat(),
            'monthly_rent': str(rental.monthly_rent),
            'currency': rental.currency,
            'deposit_amount': str(rental.deposit_amount),
            'is_active_rental': rental.is_active_rental,
            'qr_code_url': rental.qr_code_image.url if rental.qr_code_image else None,
            'url': rental.get_absolute_url(),
        })
    return JsonResponse({'rentals': data})


@login_required
def api_rental_detail(request, pk):
    """JSON API for single rental"""
    rental = get_object_or_404(Rental.objects.select_related('property_obj', 'tenant'), pk=pk)
    data = {
        'id': str(rental.pk),
        'property': rental.property_obj.name,
        'property_id': str(rental.property_obj.pk),
        'tenant': rental.tenant.name if rental.tenant else None,
        'tenant_id': str(rental.tenant.pk) if rental.tenant else None,
        'status': rental.status,
        'calculated_status': rental.get_rental_status(),
        'start_date': rental.start_date.isoformat(),
        'end_date': rental.end_date.isoformat(),
        'monthly_rent': str(rental.monthly_rent),
        'currency': rental.currency,
        'deposit_amount': str(rental.deposit_amount),
        'terms': rental.terms,
        'notes': rental.notes,
        'is_active_rental': rental.is_active_rental,
        'qr_code_url': rental.qr_code_image.url if rental.qr_code_image else None,
        'url': rental.get_absolute_url(),
    }
    return JsonResponse(data)


@login_required
def rental_agreement_detail(request, pk):
    """View rental agreement details"""
    agreement = get_object_or_404(
        RentalAgreement.objects.select_related(
            'rental__property_obj__owner', 'rental__tenant'
        ),
        pk=pk
    )
    context = {'agreement': agreement}
    return render(request, 'rentals/rental_agreement_detail.html', context)


@login_required
def rental_agreement_print(request, pk):
    """Print view for rental agreement - professional formatted page"""
    agreement = get_object_or_404(
        RentalAgreement.objects.select_related(
            'rental__property_obj__owner', 'rental__tenant'
        ),
        pk=pk
    )
    context = {'agreement': agreement}
    return render(request, 'rentals/rental_agreement_print.html', context)
