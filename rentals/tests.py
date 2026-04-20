from django.test import TestCase
from django.core.exceptions import ValidationError
from django.utils import timezone
from datetime import date, timedelta
from .models import Owner, Tenant, Property, Rental, RentalAgreement


class OwnerModelTests(TestCase):
    """Tests for Owner model"""
    
    def test_owner_creation(self):
        """Test creating an owner"""
        owner = Owner.objects.create(
            owner_type='individual',
            first_name='John',
            last_name='Doe',
            email='john@example.com',
            phone='+256700123456'
        )
        self.assertEqual(owner.name, 'John Doe')
        self.assertEqual(owner.owner_type, 'individual')
    
    def test_company_owner_name(self):
        """Test company owner name property"""
        owner = Owner.objects.create(
            owner_type='company',
            company_name='Acme Corp',
            email='info@acme.com'
        )
        self.assertEqual(owner.name, 'Acme Corp')
    
    def test_property_count(self):
        """Test property count calculation"""
        owner = Owner.objects.create(
            owner_type='individual',
            first_name='John',
            last_name='Doe'
        )
        self.assertEqual(owner.property_count, 0)
        
        # Add properties
        Property.objects.create(
            owner=owner,
            property_type='residential',
            name='Property 1',
            address='123 Main St',
            city='Kampala',
            area_sq_meters=100,
            base_rent=500000
        )
        self.assertEqual(owner.property_count, 1)
    
    def test_owner_deletion_with_active_rentals(self):
        """Test that owner with active property rentals cannot be deleted"""
        owner = Owner.objects.create(
            owner_type='individual',
            first_name='John',
            last_name='Doe'
        )
        
        tenant = Tenant.objects.create(
            tenant_type='individual',
            first_name='Jane',
            last_name='Smith'
        )
        
        property = Property.objects.create(
            owner=owner,
            property_type='residential',
            name='Property 1',
            address='123 Main St',
            city='Kampala',
            area_sq_meters=100,
            base_rent=500000
        )
        
        # Create active rental on owner's property
        Rental.objects.create(
            property_obj=property,
            tenant=tenant,
            status='active',
            start_date=date.today(),
            end_date=date.today() + timedelta(days=365),
            monthly_rent=500000
        )
        
        # Attempt to delete should raise ValidationError
        with self.assertRaises(ValidationError):
            owner.delete()


class TenantModelTests(TestCase):
    """Tests for Tenant model"""
    
    def test_tenant_creation(self):
        """Test creating a tenant"""
        tenant = Tenant.objects.create(
            tenant_type='individual',
            first_name='Jane',
            last_name='Smith',
            email='jane@example.com',
            phone='+256700654321'
        )
        self.assertEqual(tenant.name, 'Jane Smith')
        self.assertEqual(tenant.tenant_type, 'individual')
    
    def test_company_tenant_name(self):
        """Test company tenant name property"""
        tenant = Tenant.objects.create(
            tenant_type='company',
            company_name='TenantCo Ltd',
            email='info@tenantco.com'
        )
        self.assertEqual(tenant.name, 'TenantCo Ltd')
    
    def test_tenant_deletion_with_active_rentals(self):
        """Test that tenant with active rentals cannot be deleted"""
        owner = Owner.objects.create(
            owner_type='individual',
            first_name='John',
            last_name='Doe'
        )
        tenant = Tenant.objects.create(
            tenant_type='individual',
            first_name='Jane',
            last_name='Smith'
        )
        property = Property.objects.create(
            owner=owner,
            property_type='residential',
            name='Property 1',
            address='123 Main St',
            city='Kampala',
            area_sq_meters=100,
            base_rent=500000
        )
        Rental.objects.create(
            property_obj=property,
            tenant=tenant,
            status='active',
            start_date=date.today(),
            end_date=date.today() + timedelta(days=365),
            monthly_rent=500000
        )
        with self.assertRaises(ValidationError):
            tenant.delete()


class PropertyModelTests(TestCase):
    """Tests for Property model"""
    
    def test_property_creation(self):
        """Test creating a property"""
        owner = Owner.objects.create(
            owner_type='individual',
            first_name='John',
            last_name='Doe'
        )
        property = Property.objects.create(
            owner=owner,
            property_type='residential',
            name='Test Property',
            address='123 Main St',
            city='Kampala',
            area_sq_meters=100,
            base_rent=500000,
            number_of_units=3
        )
        self.assertEqual(property.name, 'Test Property')
        self.assertEqual(property.number_of_units, 3)
    
    def test_property_qr_code_generation(self):
        """Test QR code generation on property save"""
        owner = Owner.objects.create(
            owner_type='individual',
            first_name='John',
            last_name='Doe'
        )
        property = Property.objects.create(
            owner=owner,
            property_type='residential',
            name='Test Property',
            address='123 Main St',
            city='Kampala',
            area_sq_meters=100,
            base_rent=500000
        )
        # QR code should be generated on save
        self.assertIsNotNone(property.qr_code_image)


class RentalModelTests(TestCase):
    """Tests for Rental model"""
    
    def setUp(self):
        """Set up test data"""
        self.owner = Owner.objects.create(
            owner_type='individual',
            first_name='John',
            last_name='Doe'
        )
        self.tenant = Tenant.objects.create(
            tenant_type='individual',
            first_name='Jane',
            last_name='Smith'
        )
        self.property = Property.objects.create(
            owner=self.owner,
            property_type='residential',
            name='Test Property',
            address='123 Main St',
            city='Kampala',
            area_sq_meters=100,
            base_rent=500000
        )
    
    def test_rental_creation(self):
        """Test creating a rental"""
        rental = Rental.objects.create(
            property_obj=self.property,
            tenant=self.tenant,
            status='pending',
            start_date=date.today(),
            end_date=date.today() + timedelta(days=365),
            monthly_rent=500000
        )
        self.assertEqual(rental.status, 'pending')
        self.assertEqual(rental.monthly_rent, 500000)
    
    def test_is_active_rental(self):
        """Test is_active_rental property"""
        today = date.today()
        rental = Rental.objects.create(
            property_obj=self.property,
            tenant=self.tenant,
            status='active',
            start_date=today - timedelta(days=30),
            end_date=today + timedelta(days=335),
            monthly_rent=500000
        )
        self.assertTrue(rental.is_active_rental)
    
    def test_rental_status_upcoming(self):
        """Test upcoming rental status"""
        today = date.today()
        rental = Rental.objects.create(
            property_obj=self.property,
            tenant=self.tenant,
            status='pending',
            start_date=today + timedelta(days=30),
            end_date=today + timedelta(days=395),
            monthly_rent=500000
        )
        self.assertEqual(rental.get_rental_status(), 'upcoming')
    
    def test_rental_status_expired(self):
        """Test expired rental status"""
        today = date.today()
        rental = Rental.objects.create(
            property_obj=self.property,
            tenant=self.tenant,
            status='active',
            start_date=today - timedelta(days=400),
            end_date=today - timedelta(days=35),
            monthly_rent=500000
        )
        self.assertEqual(rental.get_rental_status(), 'expired')
    
    def test_rental_status_active(self):
        """Test active rental status"""
        today = date.today()
        rental = Rental.objects.create(
            property_obj=self.property,
            tenant=self.tenant,
            status='active',
            start_date=today - timedelta(days=30),
            end_date=today + timedelta(days=335),
            monthly_rent=500000
        )
        self.assertEqual(rental.get_rental_status(), 'active')
    
    def test_overlapping_rental_validation(self):
        """Test that overlapping rentals are prevented"""
        today = date.today()
        
        # Create first rental
        Rental.objects.create(
            property_obj=self.property,
            tenant=self.tenant,
            status='active',
            start_date=today,
            end_date=today + timedelta(days=365),
            monthly_rent=500000
        )
        
        # Try to create overlapping rental
        rental2 = Rental(
            property_obj=self.property,
            tenant=self.tenant,
            status='pending',
            start_date=today + timedelta(days=100),
            end_date=today + timedelta(days=400),
            monthly_rent=600000
        )
        
        with self.assertRaises(ValidationError):
            rental2.clean()
    
    def test_non_overlapping_rentals_allowed(self):
        """Test that non-overlapping rentals are allowed"""
        today = date.today()
        
        # Create first rental
        Rental.objects.create(
            property_obj=self.property,
            tenant=self.tenant,
            status='active',
            start_date=today,
            end_date=today + timedelta(days=365),
            monthly_rent=500000
        )
        
        # Create non-overlapping rental
        rental2 = Rental(
            property_obj=self.property,
            tenant=self.tenant,
            status='pending',
            start_date=today + timedelta(days=400),
            end_date=today + timedelta(days=765),
            monthly_rent=600000
        )
        
        # Should not raise ValidationError
        rental2.clean()
    
    def test_rental_qr_code_generation(self):
        """Test QR code generation on rental save"""
        rental = Rental.objects.create(
            property_obj=self.property,
            tenant=self.tenant,
            status='pending',
            start_date=date.today(),
            end_date=date.today() + timedelta(days=365),
            monthly_rent=500000
        )
        # QR code should be generated on save
        self.assertIsNotNone(rental.qr_code_image)
    
    def test_rental_with_tenant(self):
        """Test that a rental can be created with a Tenant"""
        rental = Rental(
            property_obj=self.property,
            tenant=self.tenant,
            status='pending',
            start_date=date.today(),
            end_date=date.today() + timedelta(days=365),
            monthly_rent=500000
        )
        
        # Should not raise ValidationError
        rental.clean()
    
    def test_rental_without_tenant(self):
        """Test that a rental can be created without a tenant"""
        rental = Rental(
            property_obj=self.property,
            tenant=None,  # No tenant assigned
            status='pending',
            start_date=date.today(),
            end_date=date.today() + timedelta(days=365),
            monthly_rent=500000
        )
        
        # Should not raise ValidationError
        rental.clean()
        
        # Test string representation
        self.assertIn(self.property.name, str(rental))
        self.assertIn('No tenant', str(rental))


class RentalAgreementModelTests(TestCase):
    """Tests for RentalAgreement model"""
    
    def setUp(self):
        """Set up test data"""
        self.owner = Owner.objects.create(
            owner_type='individual',
            first_name='John',
            last_name='Doe'
        )
        self.tenant = Tenant.objects.create(
            tenant_type='individual',
            first_name='Jane',
            last_name='Smith'
        )
        self.property = Property.objects.create(
            owner=self.owner,
            property_type='residential',
            name='Test Property',
            address='123 Main St',
            city='Kampala',
            area_sq_meters=100,
            base_rent=500000
        )
        self.rental = Rental.objects.create(
            property_obj=self.property,
            tenant=self.tenant,
            status='active',
            start_date=date.today(),
            end_date=date.today() + timedelta(days=365),
            monthly_rent=500000
        )
    
    def test_rental_agreement_creation(self):
        """Test creating a rental agreement"""
        agreement = RentalAgreement.objects.create(
            rental=self.rental,
            agreement_type='lease',
            title='Lease Agreement',
            effective_date=date.today(),
            rent_amount=500000,
            currency='UGX'
        )
        
        # Check that agreement number is generated
        self.assertTrue(agreement.agreement_number.startswith('RA-'))
        self.assertEqual(str(agreement), f"{agreement.title} - {agreement.agreement_number}")
    
    def test_rental_agreement_relationships(self):
        """Test rental agreement relationships"""
        agreement = RentalAgreement.objects.create(
            rental=self.rental,
            agreement_type='lease',
            title='Lease Agreement',
            effective_date=date.today(),
            rent_amount=500000,
            currency='UGX'
        )
        
        # Test relationships
        self.assertEqual(agreement.rental, self.rental)
        self.assertEqual(agreement.rental.property_obj, self.property)
        self.assertEqual(agreement.rental.tenant, self.tenant)
    
    def test_rental_agreement_choices(self):
        """Test rental agreement choice fields"""
        agreement = RentalAgreement.objects.create(
            rental=self.rental,
            agreement_type='lease',
            status='draft',
            title='Lease Agreement',
            effective_date=date.today(),
            rent_amount=500000,
            currency='UGX',
            payment_frequency='monthly'
        )
        
        self.assertEqual(agreement.agreement_type, 'lease')
        self.assertEqual(agreement.get_agreement_type_display(), 'Lease Agreement')
        self.assertEqual(agreement.status, 'draft')
        self.assertEqual(agreement.get_status_display(), 'Draft')
        self.assertEqual(agreement.payment_frequency, 'monthly')
        self.assertEqual(agreement.get_payment_frequency_display(), 'Monthly')

