from django.urls import path
from . import views

app_name = 'marketplace'

urlpatterns = [
    # Auth
    path('login/', views.marketplace_login, name='login'),
    path('register/', views.marketplace_register, name='register'),
    path('logout/', views.marketplace_logout, name='logout'),

    # Public
    path('', views.home, name='home'),
    path('rooms/', views.listing_list, name='listing_list'),
    path('rooms/<uuid:pk>/', views.listing_detail, name='listing_detail'),
    path('rooms/<uuid:pk>/qr/', views.listing_qr, name='listing_qr'),

    # Landlord
    path('rooms/post/', views.post_listing, name='post_listing'),
    path('rooms/<uuid:pk>/edit/', views.edit_listing, name='edit_listing'),
    path('rooms/<uuid:pk>/delete/', views.delete_listing, name='delete_listing'),

    # User
    path('dashboard/', views.dashboard, name='dashboard'),
    path('profile/', views.profile_edit, name='profile_edit'),

    # AJAX
    path('rooms/<uuid:pk>/save/', views.toggle_save, name='toggle_save'),
    path('photos/<uuid:photo_pk>/delete/', views.delete_photo, name='delete_photo'),
]
