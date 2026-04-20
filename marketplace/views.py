from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.models import User
from django.contrib import messages
from django.db.models import Q
from django.http import JsonResponse, HttpResponse
from django.views.decorators.http import require_POST
from django.utils import timezone
from django.urls import reverse
from urllib.parse import urlencode

from .models import MarketplaceProfile, RoomListing, ListingPhoto, SavedListing, Enquiry
from .forms import (
    MarketplaceLoginForm, MarketplaceRegisterForm,
    RoomListingForm, ListingPhotoForm, EnquiryForm, ProfileEditForm,
)


def _marketplace_user_required(request):
    if not request.user.is_authenticated:
        return False
    return hasattr(request.user, 'marketplace_profile')


# ──────────────────────────────────────────────
# Auth
# ──────────────────────────────────────────────

def marketplace_login(request):
    if request.user.is_authenticated and hasattr(request.user, 'marketplace_profile'):
        return redirect('marketplace:dashboard')

    form = MarketplaceLoginForm(request.POST or None)
    if request.method == 'POST' and form.is_valid():
        email = form.cleaned_data['email'].lower()
        password = form.cleaned_data['password']
        user = authenticate(request, email=email, password=password)
        if user and hasattr(user, 'marketplace_profile'):
            login(request, user)
            return redirect(request.GET.get('next', 'marketplace:dashboard'))
        elif user and not hasattr(user, 'marketplace_profile'):
            form.add_error(None, 'This account is not registered on the marketplace.')
        else:
            form.add_error(None, 'Invalid email or password.')

    return render(request, 'marketplace/auth/login.html', {'form': form})


def marketplace_register(request):
    form = MarketplaceRegisterForm(request.POST or None)
    if request.method == 'POST' and form.is_valid():
        data = form.cleaned_data
        user = User.objects.create_user(
            username=data['email'].lower(),
            email=data['email'].lower(),
            password=data['password1'],
            first_name=data['first_name'],
            last_name=data['last_name'],
        )
        MarketplaceProfile.objects.create(
            user=user,
            role=data['role'],
            phone=data.get('phone', ''),
            city=data.get('city', ''),
        )
        user = authenticate(request, email=data['email'].lower(), password=data['password1'])
        login(request, user)
        messages.success(request, f"Welcome, {user.first_name}! Your account has been created.")
        return redirect('marketplace:dashboard')

    return render(request, 'marketplace/auth/register.html', {'form': form})


def marketplace_logout(request):
    logout(request)
    return redirect('marketplace:home')


# ──────────────────────────────────────────────
# Public pages
# ──────────────────────────────────────────────

def home(request):
    featured = RoomListing.objects.filter(status='active').select_related('landlord__user')[:8]
    cities = (
        RoomListing.objects.filter(status='active')
        .values_list('city', flat=True)
        .distinct()
        .order_by('city')[:12]
    )
    context = {
        'featured': featured,
        'cities': cities,
        'total_listings': RoomListing.objects.filter(status='active').count(),
    }
    return render(request, 'marketplace/home.html', context)


def listing_list(request):
    qs = RoomListing.objects.filter(status='active').select_related('landlord__user').prefetch_related('photos')

    q = request.GET.get('q', '').strip()
    city = request.GET.get('city', '').strip()
    room_type = request.GET.get('room_type', '').strip()
    min_rent = request.GET.get('min_rent', '').strip()
    max_rent = request.GET.get('max_rent', '').strip()
    bills = request.GET.get('bills', '').strip()
    furnished = request.GET.get('furnished', '').strip()

    if q:
        qs = qs.filter(Q(title__icontains=q) | Q(city__icontains=q) | Q(postcode__icontains=q) | Q(description__icontains=q))
    if city:
        qs = qs.filter(city__icontains=city)
    if room_type:
        qs = qs.filter(room_type=room_type)
    if min_rent:
        try:
            qs = qs.filter(monthly_rent__gte=float(min_rent))
        except ValueError:
            pass
    if max_rent:
        try:
            qs = qs.filter(monthly_rent__lte=float(max_rent))
        except ValueError:
            pass
    if bills == '1':
        qs = qs.filter(bills_included=True)
    if furnished == '1':
        qs = qs.filter(furnished=True)
    elif furnished == '0':
        qs = qs.filter(furnished=False)

    sort = request.GET.get('sort', '-created_at')
    if sort in ['monthly_rent', '-monthly_rent', '-created_at', 'created_at']:
        qs = qs.order_by(sort)

    cities = RoomListing.objects.filter(status='active').values_list('city', flat=True).distinct().order_by('city')

    saved_ids = set()
    if request.user.is_authenticated:
        saved_ids = set(
            SavedListing.objects.filter(user=request.user).values_list('listing_id', flat=True)
        )

    context = {
        'listings': qs,
        'saved_ids': saved_ids,
        'cities': cities,
        'room_type_choices': RoomListing.ROOM_TYPE_CHOICES,
        'q': q, 'city': city, 'room_type': room_type,
        'min_rent': min_rent, 'max_rent': max_rent,
        'bills': bills, 'furnished': furnished, 'sort': sort,
        'total': qs.count(),
    }
    return render(request, 'marketplace/listing_list.html', context)


def listing_detail(request, pk):
    listing = get_object_or_404(
        RoomListing.objects.select_related('landlord__user').prefetch_related('photos', 'enquiries'),
        pk=pk,
    )
    if not listing.qr_code_image:
        listing.generate_qr_code()
        listing.save(update_fields=['qr_code_image'])

    # Track views using session to avoid count increase on refresh
    viewed_rooms = request.session.get('viewed_rooms', [])
    listing_id_str = str(pk)
    if listing_id_str not in viewed_rooms:
        RoomListing.objects.filter(pk=pk).update(views_count=listing.views_count + 1)
        viewed_rooms.append(listing_id_str)
        request.session['viewed_rooms'] = viewed_rooms

    is_saved = False
    if request.user.is_authenticated:
        is_saved = SavedListing.objects.filter(user=request.user, listing=listing).exists()

    enquiry_form = EnquiryForm()
    if request.method == 'POST' and 'send_enquiry' in request.POST:
        if not request.user.is_authenticated:
            return redirect(f"/marketplace/login/?next=/marketplace/rooms/{pk}/")
        enquiry_form = EnquiryForm(request.POST)
        if enquiry_form.is_valid():
            e = enquiry_form.save(commit=False)
            e.listing = listing
            e.sender = request.user
            e.save()
            messages.success(request, 'Your enquiry has been sent to the landlord!')
            return redirect('marketplace:listing_detail', pk=pk)

    context = {
        'listing': listing,
        'photos': listing.photos.all(),
        'is_saved': is_saved,
        'enquiry_form': enquiry_form,
        'today': timezone.now().date(),
        'qr_target_url': request.build_absolute_uri(request.get_full_path()),
        'qr_image_url': f"{reverse('marketplace:listing_qr', kwargs={'pk': listing.pk})}?{urlencode({'target': request.build_absolute_uri(request.get_full_path())})}",
        'qr_download_url': f"{reverse('marketplace:listing_qr', kwargs={'pk': listing.pk})}?{urlencode({'target': request.build_absolute_uri(request.get_full_path()), 'download': '1'})}",
        'other_listings': RoomListing.objects.filter(
            landlord=listing.landlord, status='active'
        ).exclude(pk=pk)[:3],
    }
    return render(request, 'marketplace/listing_detail.html', context)


def listing_qr(request, pk):
    listing = get_object_or_404(RoomListing, pk=pk)
    target_url = request.GET.get('target') or request.build_absolute_uri(
        reverse('marketplace:listing_detail', kwargs={'pk': listing.pk})
    )

    try:
        import qrcode
        from io import BytesIO

        qr = qrcode.QRCode(
            version=1,
            error_correction=qrcode.constants.ERROR_CORRECT_M,
            box_size=10,
            border=4,
        )
        qr.add_data(target_url)
        qr.make(fit=True)
        img = qr.make_image(fill_color='black', back_color='white')

        buffer = BytesIO()
        img.save(buffer, format='PNG')
        buffer.seek(0)

        response = HttpResponse(buffer.getvalue(), content_type='image/png')
        if request.GET.get('download') == '1':
            response['Content-Disposition'] = f'attachment; filename="room_{listing.pk}_qr.png"'
        return response
    except ImportError:
        return HttpResponse('QR library is not installed on this server.', status=500)


# ──────────────────────────────────────────────
# Landlord views
# ──────────────────────────────────────────────

def post_listing(request):
    if not _marketplace_user_required(request):
        return redirect('marketplace:login')
    profile = request.user.marketplace_profile
    if profile.role != 'landlord':
        messages.error(request, 'Only landlords can post room listings.')
        return redirect('marketplace:dashboard')

    form = RoomListingForm(request.POST or None, request.FILES or None)
    
    context = {
        'form': form,
        'edit': False
    }

    if request.method == 'POST':
        if form.is_valid():
            listing = form.save(commit=False)
            listing.landlord = profile
            listing.save()
            
            photo_files = request.FILES.getlist('photos')
            for i, f in enumerate(photo_files):
                ListingPhoto.objects.create(
                    listing=listing,
                    image=f,
                    is_primary=(i == 0),
                    order=i,
                )
            
            if request.headers.get('x-requested-with') == 'XMLHttpRequest':
                return JsonResponse({'success': True, 'message': 'Listing posted successfully.'})
            
            messages.success(request, 'Your listing has been posted!')
            return redirect('marketplace:listing_detail', pk=listing.pk)
        else:
            if request.headers.get('x-requested-with') == 'XMLHttpRequest':
                return render(request, 'marketplace/listing_form_inner.html', context, status=400)

    if request.headers.get('x-requested-with') == 'XMLHttpRequest':
        return render(request, 'marketplace/listing_form_inner.html', context)
        
    return render(request, 'marketplace/post_listing.html', context)


def edit_listing(request, pk):
    if not _marketplace_user_required(request):
        return redirect('marketplace:login')
    listing = get_object_or_404(RoomListing, pk=pk, landlord=request.user.marketplace_profile)
    form = RoomListingForm(request.POST or None, request.FILES or None, instance=listing)
    
    context = {
        'form': form, 
        'listing': listing, 
        'edit': True,
        'photos': listing.photos.all()
    }
    
    if request.method == 'POST':
        if form.is_valid():
            form.save()
            photo_files = request.FILES.getlist('photos')
            for i, f in enumerate(photo_files):
                ListingPhoto.objects.create(
                    listing=listing,
                    image=f,
                    is_primary=False,
                    order=listing.photos.count() + i,
                )
            
            if request.headers.get('x-requested-with') == 'XMLHttpRequest':
                return JsonResponse({'success': True, 'message': 'Listing updated successfully.'})
            
            messages.success(request, 'Listing updated.')
            return redirect('marketplace:listing_detail', pk=listing.pk)
        else:
            # LOG ERRORS TO CONSOLE FOR DEBUGGING
            print("FORM ERRORS:", form.errors)
            if request.headers.get('x-requested-with') == 'XMLHttpRequest':
                return render(request, 'marketplace/listing_form_inner.html', context, status=400)
            # For non-AJAX POSTs that fail validation
            messages.error(request, 'Please correct the errors below.')
    
    if request.headers.get('x-requested-with') == 'XMLHttpRequest':
        return render(request, 'marketplace/listing_form_inner.html', context)
        
    return render(request, 'marketplace/post_listing.html', context)


@require_POST
def delete_listing(request, pk):
    if not _marketplace_user_required(request):
        return redirect('marketplace:login')
    listing = get_object_or_404(RoomListing, pk=pk, landlord=request.user.marketplace_profile)
    listing.delete()
    messages.success(request, 'Listing deleted.')
    return redirect('marketplace:dashboard')


@require_POST
def delete_photo(request, photo_pk):
    if not _marketplace_user_required(request):
        return JsonResponse({'error': 'login_required'}, status=401)
    photo = get_object_or_404(ListingPhoto, pk=photo_pk)
    if photo.listing.landlord != request.user.marketplace_profile:
        return JsonResponse({'error': 'unauthorized'}, status=403)
    photo.delete()
    return JsonResponse({'success': True})


# ──────────────────────────────────────────────
# Dashboard
# ──────────────────────────────────────────────

def dashboard(request):
    if not _marketplace_user_required(request):
        return redirect('marketplace:login')

    profile = request.user.marketplace_profile

    if profile.role == 'landlord':
        my_listings = RoomListing.objects.filter(landlord=profile).prefetch_related('photos', 'enquiries')
        pending_enquiries = Enquiry.objects.filter(
            listing__landlord=profile, status='sent'
        ).select_related('sender', 'listing')
        
        # Calculate stats
        total_views = sum(l.views_count for l in my_listings)
        avg_rent = None
        if my_listings:
            avg_rent = sum(l.monthly_rent for l in my_listings) / len(my_listings)
        
        context = {
            'profile': profile,
            'my_listings': my_listings,
            'pending_enquiries': pending_enquiries,
            'active_count': my_listings.filter(status='active').count(),
            'let_count': my_listings.filter(status='let').count(),
            'total_views': total_views,
            'avg_rent': avg_rent,
        }
    else:
        saved = SavedListing.objects.filter(user=request.user).select_related('listing__landlord__user').prefetch_related('listing__photos')
        my_enquiries = Enquiry.objects.filter(sender=request.user).select_related('listing__landlord__user')
        context = {
            'profile': profile,
            'saved': saved,
            'my_enquiries': my_enquiries,
        }

    return render(request, 'marketplace/dashboard.html', context)


# ──────────────────────────────────────────────
# Profile
# ──────────────────────────────────────────────

def profile_edit(request):
    if not _marketplace_user_required(request):
        return redirect('marketplace:login')

    profile = request.user.marketplace_profile
    form = ProfileEditForm(request.POST or None, request.FILES or None, instance=profile)

    if request.method == 'POST' and form.is_valid():
        form.save()
        request.user.first_name = form.cleaned_data['first_name']
        request.user.last_name = form.cleaned_data['last_name']
        request.user.save()
        messages.success(request, 'Profile updated.')
        return redirect('marketplace:dashboard')

    return render(request, 'marketplace/profile.html', {'form': form, 'profile': profile})


# ──────────────────────────────────────────────
# AJAX actions
# ──────────────────────────────────────────────

@require_POST
def toggle_save(request, pk):
    if not request.user.is_authenticated:
        return JsonResponse({'error': 'login_required'}, status=401)
    listing = get_object_or_404(RoomListing, pk=pk)
    obj, created = SavedListing.objects.get_or_create(user=request.user, listing=listing)
    if not created:
        obj.delete()
        return JsonResponse({'saved': False})
    return JsonResponse({'saved': True})
