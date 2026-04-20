import uuid
from django.db import models
from django.contrib.auth.models import User
from django.urls import reverse


class MarketplaceProfile(models.Model):
    ROLE_CHOICES = (
        ('landlord', 'Landlord'),
        ('seeker', 'Room Seeker'),
    )

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='marketplace_profile')
    role = models.CharField(max_length=20, choices=ROLE_CHOICES)
    phone = models.CharField(max_length=30, blank=True)
    bio = models.TextField(blank=True)
    avatar = models.ImageField(upload_to='marketplace/avatars/', blank=True, null=True)
    city = models.CharField(max_length=100, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        name = self.user.get_full_name() or self.user.username
        return f"{name} ({self.get_role_display()})"

    @property
    def display_name(self):
        return self.user.get_full_name() or self.user.username


class RoomListing(models.Model):
    ROOM_TYPE_CHOICES = (
        ('single', 'Single Room'),
        ('double', 'Double Room'),
        ('en_suite', 'En-suite Room'),
        ('studio', 'Studio'),
        ('whole_property', 'Whole Property'),
    )
    PROPERTY_TYPE_CHOICES = (
        ('flat', 'Flat / Apartment'),
        ('house', 'House'),
        ('studio', 'Studio Flat'),
        ('bungalow', 'Bungalow'),
        ('shared_house', 'Shared House'),
    )
    STATUS_CHOICES = (
        ('active', 'Active'),
        ('let', 'Let Agreed'),
        ('inactive', 'Inactive'),
    )
    MIN_TERM_CHOICES = (
        ('1m', '1 month'),
        ('3m', '3 months'),
        ('6m', '6 months'),
        ('9m', '9 months'),
        ('12m', '12 months'),
        ('any', 'No minimum'),
    )
    MAX_TERM_CHOICES = (
        ('none', 'None'),
        ('1m', '1 month'),
        ('3m', '3 months'),
        ('6m', '6 months'),
        ('12m', '12 months'),
    )
    OCCUPATION_CHOICES = (
        ('any', 'Any'),
        ('professional', 'Professional'),
        ('student', 'Student'),
        ('mixed', 'Mixed'),
    )
    GENDER_CHOICES = (
        ('any', 'Any gender'),
        ('male', 'Male only'),
        ('female', 'Female only'),
        ('mixed', 'Mixed'),
    )

    CURRENCY_CHOICES = (
        ('UGX', 'UGX'),
        ('KES', 'KES'),
        ('USD', 'USD'),
        ('GBP', 'GBP'),
        ('EUR', 'EUR'),
    )

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    landlord = models.ForeignKey(
        MarketplaceProfile, on_delete=models.CASCADE, related_name='listings'
    )
    title = models.CharField(max_length=200)
    description = models.TextField()

    currency = models.CharField(max_length=3, choices=CURRENCY_CHOICES, default='UGX')
    room_type = models.CharField(max_length=20, choices=ROOM_TYPE_CHOICES, default='double')
    property_type = models.CharField(max_length=20, choices=PROPERTY_TYPE_CHOICES, default='flat')

    address = models.CharField(max_length=300)
    city = models.CharField(max_length=100)
    postcode = models.CharField(max_length=20)

    monthly_rent = models.DecimalField(max_digits=10, decimal_places=2)
    bills_included = models.BooleanField(default=False)
    deposit = models.DecimalField(max_digits=10, decimal_places=2, blank=True, null=True)

    furnished = models.BooleanField(default=True)
    available_from = models.DateField()
    min_term = models.CharField(max_length=5, choices=MIN_TERM_CHOICES, default='1m')

    current_occupants = models.PositiveIntegerField(default=0)
    max_occupants = models.PositiveIntegerField(default=2)
    max_term = models.CharField(max_length=5, choices=MAX_TERM_CHOICES, default='none', blank=True)

    smokers_ok = models.BooleanField(default=False)
    pets_ok = models.BooleanField(default=False)
    couples_ok = models.BooleanField(default=False)
    dss_ok = models.BooleanField(default=False)
    students_ok = models.BooleanField(default=True)

    has_parking = models.BooleanField(default=False)
    has_garage = models.BooleanField(default=False)
    has_garden = models.BooleanField(default=False)
    has_balcony = models.BooleanField(default=False)
    has_disabled_access = models.BooleanField(default=False)
    has_living_room = models.BooleanField(default=False)
    has_wifi = models.BooleanField(default=True)
    has_washing_machine = models.BooleanField(default=False)
    has_dishwasher = models.BooleanField(default=False)

    hh_min_age = models.PositiveIntegerField(blank=True, null=True, verbose_name='Current household min age')
    hh_max_age = models.PositiveIntegerField(blank=True, null=True, verbose_name='Current household max age')
    hh_smoker = models.BooleanField(default=False, verbose_name='Current occupants smoke')
    hh_pets = models.BooleanField(default=False, verbose_name='Current occupants have pets')
    hh_occupation = models.CharField(max_length=20, choices=OCCUPATION_CHOICES, default='any', blank=True)
    hh_university = models.CharField(max_length=200, blank=True)
    hh_gender = models.CharField(max_length=10, choices=GENDER_CHOICES, default='any', blank=True)

    preferred_occupation = models.CharField(max_length=20, choices=OCCUPATION_CHOICES, default='any', blank=True)
    references_required = models.BooleanField(default=False)
    min_preferred_age = models.PositiveIntegerField(blank=True, null=True)
    max_preferred_age = models.PositiveIntegerField(blank=True, null=True)

    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='active')
    views_count = models.PositiveIntegerField(default=0)
    qr_code_image = models.ImageField(upload_to='qr_codes/marketplace/rooms/', blank=True, null=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return self.title

    def get_absolute_url(self):
        return reverse('marketplace:listing_detail', kwargs={'pk': self.pk})

    def generate_qr_code(self):
        try:
            import qrcode
            from io import BytesIO
            from django.core.files import File
            from django.conf import settings

            base_url = getattr(settings, 'SITE_URL', '').rstrip('/') or 'http://127.0.0.1:8000'
            url = f"{base_url}{self.get_absolute_url()}"

            qr = qrcode.QRCode(
                version=1,
                error_correction=qrcode.constants.ERROR_CORRECT_M,
                box_size=10,
                border=4,
            )
            qr.add_data(url)
            qr.make(fit=True)
            img = qr.make_image(fill_color='black', back_color='white')

            buffer = BytesIO()
            img.save(buffer, format='PNG')
            buffer.seek(0)

            self.qr_code_image.save(
                f'room_{self.pk}.png',
                File(buffer),
                save=False,
            )
        except ImportError:
            pass

    def save(self, *args, **kwargs):
        is_new = self.pk is None
        super().save(*args, **kwargs)
        if is_new or not self.qr_code_image:
            self.generate_qr_code()
            super().save(update_fields=['qr_code_image'])

    @property
    def primary_photo(self):
        return self.photos.filter(is_primary=True).first() or self.photos.first()

    @property
    def saved_count(self):
        return self.saved_by.count()


class ListingPhoto(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    listing = models.ForeignKey(RoomListing, on_delete=models.CASCADE, related_name='photos')
    image = models.ImageField(upload_to='marketplace/listings/')
    caption = models.CharField(max_length=200, blank=True)
    is_primary = models.BooleanField(default=False)
    order = models.PositiveIntegerField(default=0)

    class Meta:
        ordering = ['-is_primary', 'order']

    def __str__(self):
        return f"Photo for {self.listing.title}"


class SavedListing(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='saved_listings')
    listing = models.ForeignKey(RoomListing, on_delete=models.CASCADE, related_name='saved_by')
    saved_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('user', 'listing')
        ordering = ['-saved_at']

    def __str__(self):
        return f"{self.user.username} → {self.listing.title}"


class Enquiry(models.Model):
    STATUS_CHOICES = (
        ('sent', 'Sent'),
        ('read', 'Read'),
        ('replied', 'Replied'),
    )

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    listing = models.ForeignKey(RoomListing, on_delete=models.CASCADE, related_name='enquiries')
    sender = models.ForeignKey(User, on_delete=models.CASCADE, related_name='sent_enquiries')
    message = models.TextField()
    sender_phone = models.CharField(max_length=30, blank=True)
    move_in_date = models.DateField(blank=True, null=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='sent')
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"Enquiry from {self.sender.username} on {self.listing.title}"
