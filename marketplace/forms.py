from django import forms
from django.contrib.auth.models import User
from .models import MarketplaceProfile, RoomListing, ListingPhoto, Enquiry


class MarketplaceRegisterForm(forms.Form):
    role = forms.ChoiceField(
        choices=MarketplaceProfile.ROLE_CHOICES,
        widget=forms.RadioSelect,
    )
    first_name = forms.CharField(max_length=50)
    last_name = forms.CharField(max_length=50)
    email = forms.EmailField()
    phone = forms.CharField(max_length=30, required=False)
    city = forms.CharField(max_length=100, required=False)
    password1 = forms.CharField(widget=forms.PasswordInput, label='Password', min_length=8)
    password2 = forms.CharField(widget=forms.PasswordInput, label='Confirm Password')

    def clean_email(self):
        email = self.cleaned_data['email'].lower()
        if User.objects.filter(email=email).exists():
            raise forms.ValidationError('An account with this email already exists.')
        return email

    def clean(self):
        cleaned = super().clean()
        p1 = cleaned.get('password1')
        p2 = cleaned.get('password2')
        if p1 and p2 and p1 != p2:
            raise forms.ValidationError({'password2': 'Passwords do not match.'})
        return cleaned


class MarketplaceLoginForm(forms.Form):
    email = forms.EmailField()
    password = forms.CharField(widget=forms.PasswordInput)


class RoomListingForm(forms.ModelForm):
    available_from = forms.DateField(widget=forms.DateInput(attrs={'type': 'date'}))

    class Meta:
        model = RoomListing
        fields = [
            'title', 'description', 'currency', 'room_type', 'property_type',
            'address', 'city', 'postcode',
            'monthly_rent', 'bills_included', 'deposit',
            'furnished', 'available_from', 'min_term', 'max_term',
            'current_occupants', 'max_occupants',
            'smokers_ok', 'pets_ok', 'couples_ok', 'dss_ok', 'students_ok',
            'has_parking', 'has_garage', 'has_garden', 'has_balcony',
            'has_disabled_access', 'has_living_room',
            'has_wifi', 'has_washing_machine', 'has_dishwasher',
            'hh_min_age', 'hh_max_age', 'hh_smoker', 'hh_pets',
            'hh_occupation', 'hh_university', 'hh_gender',
            'preferred_occupation', 'references_required',
            'min_preferred_age', 'max_preferred_age',
        ]
        widgets = {
            'description': forms.Textarea(attrs={'rows': 5}),
            'title': forms.TextInput(attrs={'placeholder': 'e.g. Double room in modern flat near city centre'}),
            'postcode': forms.TextInput(attrs={'placeholder': 'e.g. SW1A 1AA'}),
        }


class ListingPhotoForm(forms.ModelForm):
    class Meta:
        model = ListingPhoto
        fields = ['image', 'caption', 'is_primary']


class EnquiryForm(forms.ModelForm):
    move_in_date = forms.DateField(
        required=False,
        widget=forms.DateInput(attrs={'type': 'date'}),
        label='Preferred move-in date',
    )

    class Meta:
        model = Enquiry
        fields = ['message', 'sender_phone', 'move_in_date']
        widgets = {
            'message': forms.Textarea(attrs={
                'rows': 4,
                'placeholder': 'Hi, I am interested in this room. Could you tell me more about...',
            }),
            'sender_phone': forms.TextInput(attrs={'placeholder': 'Your phone number (optional)'}),
        }


class ProfileEditForm(forms.ModelForm):
    first_name = forms.CharField(max_length=50)
    last_name = forms.CharField(max_length=50)

    class Meta:
        model = MarketplaceProfile
        fields = ['phone', 'bio', 'avatar', 'city']
        widgets = {
            'bio': forms.Textarea(attrs={'rows': 3, 'placeholder': 'A short bio about yourself...'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if self.instance and self.instance.user_id:
            self.fields['first_name'].initial = self.instance.user.first_name
            self.fields['last_name'].initial = self.instance.user.last_name
