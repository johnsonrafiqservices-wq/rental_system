from django.urls import path
from . import views

app_name = 'rentals'

urlpatterns = [
    # Auth
    path('login/', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),

    # Dashboard
    path('', views.dashboard, name='dashboard'),
    
    # Owners
    path('owners/', views.owner_list, name='owner_list'),
    path('owners/create/', views.owner_create, name='owner_create'),
    path('owners/<uuid:pk>/', views.owner_detail, name='owner_detail'),
    
    # Tenants
    path('tenants/', views.tenant_list, name='tenant_list'),
    path('tenants/create/', views.tenant_create, name='tenant_create'),
    path('tenants/<uuid:pk>/', views.tenant_detail, name='tenant_detail'),
    
    # Properties
    path('properties/', views.property_list, name='property_list'),
    path('properties/create/', views.property_create, name='property_create'),
    path('properties/<uuid:pk>/', views.property_detail, name='property_detail'),
    
    # Rentals
    path('rentals/', views.rental_list, name='rental_list'),
    path('rentals/create/', views.rental_create, name='rental_create'),
    path('rentals/<uuid:pk>/', views.rental_detail, name='rental_detail'),
    path('rentals/<uuid:pk>/edit/', views.rental_edit, name='rental_edit'),
    path('rentals/<uuid:pk>/add-tenant/', views.add_tenant_to_rental, name='add_tenant_to_rental'),
    
    # Rental Agreements
    path('agreements/<uuid:pk>/', views.rental_agreement_detail, name='rental_agreement_detail'),
    path('agreements/<uuid:pk>/print/', views.rental_agreement_print, name='rental_agreement_print'),
    
    # JSON API Endpoints
    path('api/owners/', views.api_owners, name='api_owners'),
    path('api/owners/<uuid:pk>/', views.api_owner_detail, name='api_owner_detail'),
    path('api/tenants/', views.api_tenants, name='api_tenants'),
    path('api/tenants/<uuid:pk>/', views.api_tenant_detail, name='api_tenant_detail'),
    path('api/properties/', views.api_properties, name='api_properties'),
    path('api/properties/<uuid:pk>/', views.api_property_detail, name='api_property_detail'),
    path('api/rentals/', views.api_rentals, name='api_rentals'),
    path('api/rentals/<uuid:pk>/', views.api_rental_detail, name='api_rental_detail'),
]
