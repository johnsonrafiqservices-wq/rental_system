from django.contrib import admin
from .models import Owner, Tenant, Property, QRCode, Rental


@admin.register(Owner)
class OwnerAdmin(admin.ModelAdmin):
    list_display = ['name', 'owner_type', 'email', 'phone', 'city', 'property_count', 'created_at']
    list_filter = ['owner_type', 'city', 'country', 'created_at']
    search_fields = ['company_name', 'first_name', 'last_name', 'email', 'phone', 'registration_number', 'national_id']
    readonly_fields = ['id', 'created_at', 'updated_at', 'property_count']
    
    fieldsets = (
        ('Owner Type', {
            'fields': ('owner_type',)
        }),
        ('Company Information', {
            'fields': ('company_name', 'registration_number', 'tax_id'),
            'classes': ('collapse',),
        }),
        ('Individual Information', {
            'fields': ('first_name', 'last_name', 'national_id'),
            'classes': ('collapse',),
        }),
        ('Contact Information', {
            'fields': ('email', 'phone', 'address', 'city', 'country')
        }),
        ('System Information', {
            'fields': ('id', 'created_at', 'updated_at', 'property_count'),
            'classes': ('collapse',),
        }),
    )


@admin.register(Tenant)
class TenantAdmin(admin.ModelAdmin):
    list_display = ['name', 'tenant_type', 'email', 'phone', 'city', 'rental_count', 'created_at']
    list_filter = ['tenant_type', 'city', 'country', 'created_at']
    search_fields = ['company_name', 'first_name', 'last_name', 'email', 'phone', 'registration_number', 'national_id']
    readonly_fields = ['id', 'created_at', 'updated_at', 'rental_count']
    
    fieldsets = (
        ('Tenant Type', {
            'fields': ('tenant_type',)
        }),
        ('Company Information', {
            'fields': ('company_name', 'registration_number', 'tax_id'),
            'classes': ('collapse',),
        }),
        ('Individual Information', {
            'fields': ('first_name', 'last_name', 'national_id'),
            'classes': ('collapse',),
        }),
        ('Contact Information', {
            'fields': ('email', 'phone', 'address', 'city', 'country')
        }),
        ('System Information', {
            'fields': ('id', 'created_at', 'updated_at', 'rental_count'),
            'classes': ('collapse',),
        }),
    )


class PropertyInline(admin.TabularInline):
    model = Property
    extra = 0
    fields = ['name', 'property_type', 'address', 'city', 'base_rent', 'is_active', 'is_available']
    readonly_fields = ['id']


@admin.register(Property)
class PropertyAdmin(admin.ModelAdmin):
    list_display = ['name', 'owner', 'property_type', 'address', 'city', 'base_rent', 'is_active', 'is_available', 'created_at']
    list_filter = ['property_type', 'city', 'country', 'is_active', 'is_available', 'created_at']
    search_fields = ['name', 'address', 'city', 'owner__company_name', 'owner__first_name', 'owner__last_name']
    readonly_fields = ['id', 'created_at', 'updated_at']
    
    fieldsets = (
        ('Basic Information', {
            'fields': ('owner', 'property_type', 'name', 'description')
        }),
        ('Location', {
            'fields': ('address', 'city', 'state_province', 'postal_code', 'country', 'latitude', 'longitude')
        }),
        ('Property Details', {
            'fields': ('area_sq_meters', 'number_of_rooms', 'number_of_bathrooms', 'floor_number')
        }),
        ('Financial', {
            'fields': ('base_rent', 'currency')
        }),
        ('Status', {
            'fields': ('is_active', 'is_available')
        }),
        ('System Information', {
            'fields': ('id', 'created_at', 'updated_at'),
            'classes': ('collapse',),
        }),
    )


@admin.register(QRCode)
class QRCodeAdmin(admin.ModelAdmin):
    list_display = ['property_obj', 'unique_identifier', 'generated_at']
    list_filter = ['generated_at']
    search_fields = ['property_obj__name', 'unique_identifier']
    readonly_fields = ['id', 'qr_code_image', 'unique_identifier', 'generated_at']


@admin.register(Rental)
class RentalAdmin(admin.ModelAdmin):
    list_display = ['property_obj', 'tenant', 'status', 'start_date', 'end_date', 'monthly_rent', 'is_active_rental', 'created_at']
    list_filter = ['status', 'start_date', 'end_date', 'created_at']
    search_fields = ['property_obj__name', 'tenant__first_name', 'tenant__last_name', 'tenant__company_name']
    readonly_fields = ['id', 'created_at', 'updated_at', 'is_active_rental']
    
    fieldsets = (
        ('Rental Details', {
            'fields': ('property_obj', 'tenant', 'status')
        }),
        ('Dates', {
            'fields': ('start_date', 'end_date')
        }),
        ('Financial', {
            'fields': ('monthly_rent', 'currency', 'deposit_amount')
        }),
        ('Terms & Notes', {
            'fields': ('terms', 'notes')
        }),
        ('System Information', {
            'fields': ('id', 'created_at', 'updated_at', 'is_active_rental'),
            'classes': ('collapse',),
        }),
    )
