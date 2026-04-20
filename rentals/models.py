from django.db import models
from django.core.validators import MinValueValidator
from django.core.exceptions import ValidationError
from django.urls import reverse
from datetime import date
import uuid

CURRENCY_CHOICES = [
    ('UGX', 'UGX – Ugandan Shilling'),
    ('USD', 'USD – US Dollar'),
    ('EUR', 'EUR – Euro'),
    ('GBP', 'GBP – British Pound'),
    ('KES', 'KES – Kenyan Shilling'),
    ('TZS', 'TZS – Tanzanian Shilling'),
    ('RWF', 'RWF – Rwandan Franc'),
    ('ETB', 'ETB – Ethiopian Birr'),
    ('ZAR', 'ZAR – South African Rand'),
    ('NGN', 'NGN – Nigerian Naira'),
    ('AED', 'AED – UAE Dirham'),
    ('INR', 'INR – Indian Rupee'),
    ('CNY', 'CNY – Chinese Yuan'),
    ('CAD', 'CAD – Canadian Dollar'),
    ('AUD', 'AUD – Australian Dollar'),
    ('CHF', 'CHF – Swiss Franc'),
]


class Owner(models.Model):
    """Owner can be either a Company or an Individual"""
    OWNER_TYPES = (
        ('company', 'Company'),
        ('individual', 'Individual'),
    )
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    owner_type = models.CharField(max_length=20, choices=OWNER_TYPES, default='individual')
    
    # Company fields
    company_name = models.CharField(max_length=255, blank=True, null=True)
    registration_number = models.CharField(max_length=100, blank=True, null=True)
    tax_id = models.CharField(max_length=50, blank=True, null=True)
    
    # Individual fields
    first_name = models.CharField(max_length=100, blank=True, null=True)
    last_name = models.CharField(max_length=100, blank=True, null=True)
    national_id = models.CharField(max_length=50, blank=True, null=True)
    
    # Common fields
    email = models.EmailField(blank=True, null=True)
    phone = models.CharField(max_length=20, blank=True, null=True)
    address = models.TextField(blank=True, null=True)
    city = models.CharField(max_length=100, blank=True, null=True)
    country = models.CharField(max_length=100, blank=True, null=True)
    
    # QR Code
    qr_code_image = models.ImageField(upload_to='qr_codes/owner/', blank=True, null=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    @property
    def name(self):
        if self.owner_type == 'company':
            return self.company_name or 'Unnamed Company'
        return f"{self.first_name or ''} {self.last_name or ''}".strip() or 'Unnamed Individual'
    
    @property
    def property_count(self):
        """Self-calculated number of properties for this owner"""
        return self.properties.filter(is_active=True).count()
    
    def get_absolute_url(self):
        """Get the absolute URL for this owner"""
        return reverse('rentals:owner_detail', kwargs={'pk': self.pk})
    
    def generate_qr_code(self):
        """Generate QR code for this owner"""
        try:
            import qrcode
            from io import BytesIO
            from django.core.files import File
            from django.conf import settings
            
            url = f"{settings.SITE_URL}{self.get_absolute_url()}"
            
            qr = qrcode.QRCode(
                version=1,
                error_correction=qrcode.constants.ERROR_CORRECT_L,
                box_size=10,
                border=4,
            )
            qr.add_data(url)
            qr.make(fit=True)
            img = qr.make_image(fill_color="black", back_color="white")
            
            buffer = BytesIO()
            img.save(buffer, format='PNG')
            buffer.seek(0)
            
            self.qr_code_image.save(
                f'owner_{self.pk}.png',
                File(buffer),
                save=False
            )
        except ImportError:
            pass
    
    def save(self, *args, **kwargs):
        is_new = self.pk is None
        super().save(*args, **kwargs)
        if is_new or not self.qr_code_image:
            self.generate_qr_code()
            super().save(update_fields=['qr_code_image'])
    
    def delete(self, *args, **kwargs):
        """Prevent deletion if owner has active property rentals"""
        from django.db.models import Q
        active_rentals = Rental.objects.filter(
            property_obj__owner=self, status='active'
        )
        if active_rentals.exists():
            raise ValidationError("Cannot delete owner with active property rentals.")
        super().delete(*args, **kwargs)
    
    def __str__(self):
        return f"{self.name} ({self.get_owner_type_display()})"


class Tenant(models.Model):
    """Tenant who rents a property - separate from Owner"""
    TENANT_TYPES = (
        ('company', 'Company'),
        ('individual', 'Individual'),
    )
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    tenant_type = models.CharField(max_length=20, choices=TENANT_TYPES, default='individual')
    
    # Company fields
    company_name = models.CharField(max_length=255, blank=True, null=True)
    registration_number = models.CharField(max_length=100, blank=True, null=True)
    tax_id = models.CharField(max_length=50, blank=True, null=True)
    
    # Individual fields
    first_name = models.CharField(max_length=100, blank=True, null=True)
    last_name = models.CharField(max_length=100, blank=True, null=True)
    national_id = models.CharField(max_length=50, blank=True, null=True)
    
    # Common fields
    email = models.EmailField(blank=True, null=True)
    phone = models.CharField(max_length=20, blank=True, null=True)
    address = models.TextField(blank=True, null=True)
    city = models.CharField(max_length=100, blank=True, null=True)
    country = models.CharField(max_length=100, blank=True, null=True)
    
    # QR Code
    qr_code_image = models.ImageField(upload_to='qr_codes/tenant/', blank=True, null=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    @property
    def name(self):
        if self.tenant_type == 'company':
            return self.company_name or 'Unnamed Company'
        return f"{self.first_name or ''} {self.last_name or ''}".strip() or 'Unnamed Individual'
    
    @property
    def rental_count(self):
        """Number of rentals for this tenant"""
        return self.rentals.count()
    
    def get_absolute_url(self):
        return reverse('rentals:tenant_detail', kwargs={'pk': self.pk})
    
    def generate_qr_code(self):
        """Generate QR code for this tenant"""
        try:
            import qrcode
            from io import BytesIO
            from django.core.files import File
            from django.conf import settings
            
            url = f"{settings.SITE_URL}{self.get_absolute_url()}"
            
            qr = qrcode.QRCode(
                version=1,
                error_correction=qrcode.constants.ERROR_CORRECT_L,
                box_size=10,
                border=4,
            )
            qr.add_data(url)
            qr.make(fit=True)
            img = qr.make_image(fill_color="black", back_color="white")
            
            buffer = BytesIO()
            img.save(buffer, format='PNG')
            buffer.seek(0)
            
            self.qr_code_image.save(
                f'tenant_{self.pk}.png',
                File(buffer),
                save=False
            )
        except ImportError:
            pass
    
    def save(self, *args, **kwargs):
        is_new = self.pk is None
        super().save(*args, **kwargs)
        if is_new or not self.qr_code_image:
            self.generate_qr_code()
            super().save(update_fields=['qr_code_image'])
    
    def delete(self, *args, **kwargs):
        """Prevent deletion if tenant has active rentals"""
        active_rentals = self.rentals.filter(status='active')
        if active_rentals.exists():
            raise ValidationError("Cannot delete tenant with active rentals.")
        super().delete(*args, **kwargs)
    
    def __str__(self):
        return f"{self.name} ({self.get_tenant_type_display()})"


class Property(models.Model):
    """Rentable property with location"""
    PROPERTY_TYPES = (
        ('residential', 'Residential'),
        ('commercial', 'Commercial'),
        ('industrial', 'Industrial'),
        ('land', 'Land'),
        ('parking', 'Parking Space'),
        ('storage', 'Storage Unit'),
        ('other', 'Other'),
    )
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    owner = models.ForeignKey(Owner, on_delete=models.CASCADE, related_name='properties')
    
    property_type = models.CharField(max_length=20, choices=PROPERTY_TYPES)
    name = models.CharField(max_length=255)
    description = models.TextField(blank=True, null=True)
    
    # Location
    address = models.CharField(max_length=255)
    city = models.CharField(max_length=100)
    state_province = models.CharField(max_length=100, blank=True, null=True)
    postal_code = models.CharField(max_length=20, blank=True, null=True)
    country = models.CharField(max_length=100, default='Uganda')
    latitude = models.DecimalField(max_digits=9, decimal_places=6, blank=True, null=True)
    longitude = models.DecimalField(max_digits=9, decimal_places=6, blank=True, null=True)
    
    # Property details
    area_sq_meters = models.DecimalField(max_digits=10, decimal_places=2, validators=[MinValueValidator(0)])
    number_of_units = models.IntegerField(default=1, validators=[MinValueValidator(1)], help_text='Number of rentable units in this property')
    
    # QR Code
    qr_code_image = models.ImageField(upload_to='qr_codes/property/', blank=True, null=True)
    
    # Financial
    base_rent = models.DecimalField(max_digits=12, decimal_places=2, validators=[MinValueValidator(0)])
    currency = models.CharField(max_length=3, choices=CURRENCY_CHOICES, default='UGX')
    
    # Status
    is_active = models.BooleanField(default=True)
    is_available = models.BooleanField(default=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-created_at']
    
    def get_absolute_url(self):
        """Get the absolute URL for this property"""
        return reverse('rentals:property_detail', kwargs={'pk': self.pk})
    
    def generate_qr_code(self):
        """Generate QR code for this property"""
        try:
            import qrcode
            from io import BytesIO
            from django.core.files import File
            from django.conf import settings
            
            url = f"{settings.SITE_URL}{self.get_absolute_url()}"
            
            qr = qrcode.QRCode(
                version=1,
                error_correction=qrcode.constants.ERROR_CORRECT_L,
                box_size=10,
                border=4,
            )
            qr.add_data(url)
            qr.make(fit=True)
            img = qr.make_image(fill_color="black", back_color="white")
            
            buffer = BytesIO()
            img.save(buffer, format='PNG')
            buffer.seek(0)
            
            self.qr_code_image.save(
                f'property_{self.pk}.png',
                File(buffer),
                save=False
            )
        except ImportError:
            pass
    
    def save(self, *args, **kwargs):
        is_new = self.pk is None
        super().save(*args, **kwargs)
        if is_new or not self.qr_code_image:
            self.generate_qr_code()
            super().save(update_fields=['qr_code_image'])
    
    def __str__(self):
        return f"{self.name} - {self.address}"


class QRCode(models.Model):
    """QR code for each registered object/property"""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    property_obj = models.OneToOneField(Property, on_delete=models.CASCADE, related_name='qr_code')
    
    qr_code_image = models.ImageField(upload_to='qr_codes/')
    unique_identifier = models.CharField(max_length=255, unique=True)
    generated_at = models.DateTimeField(auto_now_add=True)
    
    def save(self, *args, **kwargs):
        # Generate QR code with property details
        if not self.unique_identifier:
            self.unique_identifier = str(uuid.uuid4())
        
        # Generate QR code (lazy import to avoid requiring qrcode for migrations)
        try:
            import qrcode
            from io import BytesIO
            from django.core.files import File
            
            qr_data = {
                'property_id': str(self.property_obj.id),
                'property_name': self.property_obj.name,
                'address': self.property_obj.address,
                'unique_id': self.unique_identifier,
            }
            
            qr = qrcode.QRCode(
                version=1,
                error_correction=qrcode.constants.ERROR_CORRECT_L,
                box_size=10,
                border=4,
            )
            
            qr.add_data(str(qr_data))
            qr.make(fit=True)
            
            img = qr.make_image(fill_color="black", back_color="white")
            
            # Save to BytesIO
            buffer = BytesIO()
            img.save(buffer, format='PNG')
            buffer.seek(0)
            
            # Save to ImageField
            self.qr_code_image.save(
                f'qr_{self.unique_identifier}.png',
                File(buffer),
                save=False
            )
        except ImportError:
            # If qrcode is not installed, skip QR generation
            pass
        
        super().save(*args, **kwargs)
    
    def __str__(self):
        return f"QR Code for {self.property_obj.name}"


class Rental(models.Model):
    """Rental agreement for a property"""
    STATUS_CHOICES = (
        ('pending', 'Pending'),
        ('active', 'Active'),
        ('expired', 'Expired'),
        ('terminated', 'Terminated'),
    )
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    rental_number = models.CharField(max_length=20, unique=True, blank=True)
    name = models.CharField(max_length=200, blank=True)
    property_obj = models.ForeignKey(Property, on_delete=models.CASCADE, related_name='rentals')
    
    tenant = models.ForeignKey(
        Tenant,
        on_delete=models.CASCADE,
        related_name='rentals',
        null=True,
        blank=True
    )
    
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    
    start_date = models.DateField(default=date.today)
    end_date = models.DateField(null=True, blank=True)
    
    PAYMENT_FREQUENCY_CHOICES = (
        ('monthly', 'Monthly'),
        ('quarterly', 'Quarterly'),
        ('weekly', 'Weekly'),
        ('annually', 'Annually'),
    )

    monthly_rent = models.DecimalField(max_digits=12, decimal_places=2, validators=[MinValueValidator(0)])
    currency = models.CharField(max_length=3, choices=CURRENCY_CHOICES, default='UGX')
    payment_frequency = models.CharField(max_length=20, choices=PAYMENT_FREQUENCY_CHOICES, default='monthly')
    
    deposit_amount = models.DecimalField(max_digits=12, decimal_places=2, validators=[MinValueValidator(0)], default=0)
    
    # Room details
    number_of_rooms = models.IntegerField(blank=True, null=True)
    number_of_bathrooms = models.IntegerField(blank=True, null=True)
    floor_number = models.IntegerField(blank=True, null=True)
    
    terms = models.TextField(blank=True, null=True)
    notes = models.TextField(blank=True, null=True)
    
    # QR Code
    qr_code_image = models.ImageField(upload_to='qr_codes/rental/', blank=True, null=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-created_at']
    
    @property
    def is_active_rental(self):
        from django.utils import timezone
        today = timezone.now().date()
        if self.end_date:
            return self.status == 'active' and self.start_date <= today <= self.end_date
        return self.status == 'active' and self.start_date <= today
    
    def get_absolute_url(self):
        """Get the absolute URL for this rental"""
        return reverse('rentals:rental_detail', kwargs={'pk': self.pk})
    
    def get_rental_status(self):
        """Get calculated rental status (active/expired/upcoming)"""
        from django.utils import timezone
        today = timezone.now().date()
        
        if self.status == 'terminated':
            return 'terminated'
        elif today < self.start_date:
            return 'upcoming'
        elif self.end_date and today > self.end_date:
            return 'expired'
        elif self.status == 'active':
            return 'active'
        else:
            return 'pending'
    
    def clean(self):
        """Validate rental dates don't overlap"""
        from django.core.exceptions import ValidationError
        
        # Check for overlapping rentals on the same property
        if self.end_date:
            overlapping_rentals = Rental.objects.filter(
                property_obj=self.property_obj
            ).exclude(pk=self.pk).filter(
                status__in=['pending', 'active']
            ).filter(
                start_date__lte=self.end_date,
                end_date__gte=self.start_date
            )
            if overlapping_rentals.exists():
                raise ValidationError(
                    'This property has an overlapping rental during the specified period.'
                )
    
    def generate_qr_code(self):
        """Generate QR code for this rental — encodes direct URL to rental detail page"""
        try:
            import qrcode
            from io import BytesIO
            from django.core.files import File
            from django.conf import settings
            
            url = f"{settings.SITE_URL}{self.get_absolute_url()}"
            
            qr = qrcode.QRCode(
                version=1,
                error_correction=qrcode.constants.ERROR_CORRECT_M,
                box_size=10,
                border=4,
            )
            qr.add_data(url)
            qr.make(fit=True)
            img = qr.make_image(fill_color="black", back_color="white")
            
            buffer = BytesIO()
            img.save(buffer, format='PNG')
            buffer.seek(0)
            
            self.qr_code_image.save(
                f'rental_{self.pk}.png',
                File(buffer),
                save=False
            )
        except ImportError:
            pass
    
    def save(self, *args, **kwargs):
        is_new = self.pk is None
        if not self.rental_number:
            last = Rental.objects.order_by('-created_at').first()
            next_num = 1
            if last and last.rental_number:
                try:
                    next_num = int(last.rental_number.replace('RNT-', '')) + 1
                except ValueError:
                    next_num = Rental.objects.count() + 1
            self.rental_number = f'RNT-{next_num:05d}'
        super().save(*args, **kwargs)
        if is_new or not self.qr_code_image:
            self.generate_qr_code()
            super().save(update_fields=['qr_code_image'])
    
    def __str__(self):
        display = self.name if self.name else (self.tenant.name if self.tenant else 'No tenant')
        return f"{self.rental_number} - {self.property_obj.name} ({display})"


class RentalAgreement(models.Model):
    """Rental agreement document linked to a rental"""
    AGREEMENT_TYPES = (
        ('lease', 'Lease Agreement'),
        ('tenancy', 'Tenancy Agreement'),
        ('sublease', 'Sublease Agreement'),
        ('room_rental', 'Room Rental Agreement'),
        ('commercial', 'Commercial Lease'),
        ('other', 'Other Agreement'),
    )
    
    STATUS_CHOICES = (
        ('draft', 'Draft'),
        ('pending_signature', 'Pending Signature'),
        ('signed', 'Signed'),
        ('active', 'Active'),
        ('expired', 'Expired'),
        ('terminated', 'Terminated'),
    )
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    rental = models.ForeignKey(Rental, on_delete=models.CASCADE, related_name='agreements')
    
    agreement_type = models.CharField(max_length=20, choices=AGREEMENT_TYPES, default='lease')
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='draft')
    
    # Agreement details
    title = models.CharField(max_length=255)
    agreement_number = models.CharField(max_length=50, unique=True, blank=True)
    
    # Dates
    effective_date = models.DateField()
    expiry_date = models.DateField(blank=True, null=True)
    signed_date = models.DateField(blank=True, null=True)
    
    # Financial terms
    rent_amount = models.DecimalField(max_digits=12, decimal_places=2, validators=[MinValueValidator(0)])
    currency = models.CharField(max_length=3, default='UGX')
    payment_frequency = models.CharField(max_length=20, choices=[
        ('monthly', 'Monthly'),
        ('quarterly', 'Quarterly'),
        ('annually', 'Annually'),
        ('weekly', 'Weekly'),
    ], default='monthly')
    
    # Security deposit
    security_deposit = models.DecimalField(max_digits=12, decimal_places=2, validators=[MinValueValidator(0)], default=0)
    deposit_paid = models.BooleanField(default=False)
    
    # Terms and conditions
    terms = models.TextField(blank=True, null=True)
    special_conditions = models.TextField(blank=True, null=True)
    
    # Document upload
    agreement_file = models.FileField(upload_to='rental_agreements/', blank=True, null=True)
    
    # Signatures
    tenant_signature = models.ImageField(upload_to='signatures/tenant/', blank=True, null=True)
    landlord_signature = models.ImageField(upload_to='signatures/landlord/', blank=True, null=True)
    witness_signature = models.ImageField(upload_to='signatures/witness/', blank=True, null=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-created_at']
    
    def get_absolute_url(self):
        """Get the absolute URL for this rental agreement"""
        return reverse('rentals:rental_agreement_detail', kwargs={'pk': self.pk})
    
    def save(self, *args, **kwargs):
        # Generate agreement number if not provided
        if not self.agreement_number:
            from django.utils import timezone
            year = timezone.now().year
            count = RentalAgreement.objects.filter(created_at__year=year).count()
            self.agreement_number = f"RA-{year}-{count + 1:04d}"
        
        super().save(*args, **kwargs)
    
    def __str__(self):
        return f"{self.title} - {self.agreement_number}"
