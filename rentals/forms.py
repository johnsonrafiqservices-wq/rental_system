from django import forms
from .models import Owner, Tenant, Property, Rental


class OwnerForm(forms.ModelForm):
    """Form for registering companies or individuals"""
    
    class Meta:
        model = Owner
        fields = [
            'owner_type',
            'company_name', 'registration_number', 'tax_id',
            'first_name', 'last_name', 'national_id',
            'email', 'phone', 'address', 'city', 'country'
        ]
        widgets = {
            'owner_type': forms.Select(attrs={'class': 'form-select'}),
            'company_name': forms.TextInput(attrs={'class': 'form-control'}),
            'registration_number': forms.TextInput(attrs={'class': 'form-control'}),
            'tax_id': forms.TextInput(attrs={'class': 'form-control'}),
            'first_name': forms.TextInput(attrs={'class': 'form-control'}),
            'last_name': forms.TextInput(attrs={'class': 'form-control'}),
            'national_id': forms.TextInput(attrs={'class': 'form-control'}),
            'email': forms.EmailInput(attrs={'class': 'form-control'}),
            'phone': forms.TextInput(attrs={'class': 'form-control'}),
            'address': forms.Textarea(attrs={'class': 'form-control', 'rows': 2}),
            'city': forms.TextInput(attrs={'class': 'form-control'}),
            'country': forms.TextInput(attrs={'class': 'form-control'}),
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Set required fields based on owner type
        if 'owner_type' in self.data:
            owner_type = self.data['owner_type']
            if owner_type == 'company':
                self.fields['company_name'].required = True
                self.fields['first_name'].required = False
                self.fields['last_name'].required = False
            else:
                self.fields['first_name'].required = True
                self.fields['last_name'].required = True
                self.fields['company_name'].required = False


class TenantForm(forms.ModelForm):
    """Form for registering tenants"""
    
    class Meta:
        model = Tenant
        fields = [
            'tenant_type',
            'company_name', 'registration_number', 'tax_id',
            'first_name', 'last_name', 'national_id',
            'email', 'phone', 'address', 'city', 'country'
        ]
        widgets = {
            'tenant_type': forms.Select(attrs={'class': 'form-select'}),
            'company_name': forms.TextInput(attrs={'class': 'form-control'}),
            'registration_number': forms.TextInput(attrs={'class': 'form-control'}),
            'tax_id': forms.TextInput(attrs={'class': 'form-control'}),
            'first_name': forms.TextInput(attrs={'class': 'form-control'}),
            'last_name': forms.TextInput(attrs={'class': 'form-control'}),
            'national_id': forms.TextInput(attrs={'class': 'form-control'}),
            'email': forms.EmailInput(attrs={'class': 'form-control'}),
            'phone': forms.TextInput(attrs={'class': 'form-control'}),
            'address': forms.Textarea(attrs={'class': 'form-control', 'rows': 2}),
            'city': forms.TextInput(attrs={'class': 'form-control'}),
            'country': forms.TextInput(attrs={'class': 'form-control'}),
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if 'tenant_type' in self.data:
            tenant_type = self.data['tenant_type']
            if tenant_type == 'company':
                self.fields['company_name'].required = True
                self.fields['first_name'].required = False
                self.fields['last_name'].required = False
            else:
                self.fields['first_name'].required = True
                self.fields['last_name'].required = True
                self.fields['company_name'].required = False


class PropertyForm(forms.ModelForm):
    """Form for creating/editing properties"""
    
    class Meta:
        model = Property
        fields = [
            'owner', 'property_type', 'name', 'description',
            'address', 'city', 'state_province', 'postal_code', 'country',
            'latitude', 'longitude',
            'area_sq_meters', 'number_of_units',
            'base_rent', 'currency', 'is_active', 'is_available'
        ]
        widgets = {
            'owner': forms.Select(attrs={'class': 'form-select'}),
            'property_type': forms.Select(attrs={'class': 'form-select'}),
            'name': forms.TextInput(attrs={'class': 'form-control'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'address': forms.TextInput(attrs={'class': 'form-control'}),
            'city': forms.TextInput(attrs={'class': 'form-control'}),
            'state_province': forms.TextInput(attrs={'class': 'form-control'}),
            'postal_code': forms.TextInput(attrs={'class': 'form-control'}),
            'country': forms.TextInput(attrs={'class': 'form-control'}),
            'latitude': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.000001'}),
            'longitude': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.000001'}),
            'area_sq_meters': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'number_of_units': forms.NumberInput(attrs={'class': 'form-control'}),
            'base_rent': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'currency': forms.TextInput(attrs={'class': 'form-control'}),
            'is_active': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'is_available': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }


class RentalForm(forms.ModelForm):
    """Form for registering a rental (tenant added separately from rental detail)"""
    
    class Meta:
        model = Rental
        fields = [
            'name', 'property_obj', 'status',
            'monthly_rent', 'currency', 'payment_frequency', 'deposit_amount',
            'number_of_rooms', 'number_of_bathrooms', 'floor_number',
            'terms', 'notes'
        ]
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'e.g. Unit 4A – Ground Floor'}),
            'property_obj': forms.Select(attrs={'class': 'form-select'}),
            'status': forms.Select(attrs={'class': 'form-select'}),
            'monthly_rent': forms.NumberInput(attrs={'step': '0.01', 'class': 'form-control', 'placeholder': '0.00'}),
            'currency': forms.Select(attrs={'class': 'form-select'}),
            'payment_frequency': forms.Select(attrs={'class': 'form-select'}),
            'deposit_amount': forms.NumberInput(attrs={'step': '0.01', 'class': 'form-control', 'placeholder': '0.00'}),
            'number_of_rooms': forms.NumberInput(attrs={'class': 'form-control', 'placeholder': 'e.g. 3'}),
            'number_of_bathrooms': forms.NumberInput(attrs={'class': 'form-control', 'placeholder': 'e.g. 1'}),
            'floor_number': forms.NumberInput(attrs={'class': 'form-control', 'placeholder': 'e.g. 2'}),
            'terms': forms.Textarea(attrs={'rows': 3, 'class': 'form-control'}),
            'notes': forms.Textarea(attrs={'rows': 2, 'class': 'form-control'}),
        }
    
    def clean(self):
        return super().clean()


