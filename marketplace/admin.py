from django.contrib import admin
from .models import MarketplaceProfile, RoomListing, ListingPhoto, SavedListing, Enquiry


@admin.register(MarketplaceProfile)
class MarketplaceProfileAdmin(admin.ModelAdmin):
    list_display = ['display_name', 'role', 'city', 'created_at']
    list_filter = ['role']
    search_fields = ['user__email', 'user__first_name', 'user__last_name']


class ListingPhotoInline(admin.TabularInline):
    model = ListingPhoto
    extra = 1


@admin.register(RoomListing)
class RoomListingAdmin(admin.ModelAdmin):
    list_display = ['title', 'city', 'monthly_rent', 'room_type', 'status', 'created_at']
    list_filter = ['status', 'room_type', 'property_type', 'city']
    search_fields = ['title', 'city', 'postcode', 'landlord__user__email']
    inlines = [ListingPhotoInline]


@admin.register(SavedListing)
class SavedListingAdmin(admin.ModelAdmin):
    list_display = ['user', 'listing', 'saved_at']


@admin.register(Enquiry)
class EnquiryAdmin(admin.ModelAdmin):
    list_display = ['sender', 'listing', 'status', 'created_at']
    list_filter = ['status']
