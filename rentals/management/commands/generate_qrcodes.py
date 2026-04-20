from django.core.management.base import BaseCommand
from django.core.management import call_command
from rentals.models import Owner, Property, Rental


class Command(BaseCommand):
    help = 'Regenerate QR codes for all owners, properties, and rentals'

    def add_arguments(self, parser):
        parser.add_argument(
            '--force',
            action='store_true',
            help='Force regeneration even if QR code exists',
        )
        parser.add_argument(
            '--type',
            type=str,
            choices=['owner', 'property', 'rental', 'all'],
            default='all',
            help='Type of QR codes to generate (default: all)',
        )

    def handle(self, *args, **options):
        force = options.get('force', False)
        qr_type = options.get('type', 'all')

        self.stdout.write(self.style.SUCCESS('Starting QR code generation...'))

        if qr_type in ['owner', 'all']:
            self.generate_owner_qrcodes(force)

        if qr_type in ['property', 'all']:
            self.generate_property_qrcodes(force)

        if qr_type in ['rental', 'all']:
            self.generate_rental_qrcodes(force)

        self.stdout.write(self.style.SUCCESS('QR code generation complete!'))

    def generate_owner_qrcodes(self, force):
        """Generate QR codes for all owners"""
        owners = Owner.objects.all()
        count = 0
        for owner in owners:
            if force or not owner.qr_code_image:
                owner.generate_qr_code()
                owner.save(update_fields=['qr_code_image'])
                count += 1
                self.stdout.write(f'Generated QR code for owner: {owner.name}')
        self.stdout.write(self.style.SUCCESS(f'Generated {count} owner QR codes'))

    def generate_property_qrcodes(self, force):
        """Generate QR codes for all properties"""
        properties = Property.objects.all()
        count = 0
        for property in properties:
            if force or not property.qr_code_image:
                property.generate_qr_code()
                property.save(update_fields=['qr_code_image'])
                count += 1
                self.stdout.write(f'Generated QR code for property: {property.name}')
        self.stdout.write(self.style.SUCCESS(f'Generated {count} property QR codes'))

    def generate_rental_qrcodes(self, force):
        """Generate QR codes for all rentals"""
        rentals = Rental.objects.all()
        count = 0
        for rental in rentals:
            if force or not rental.qr_code_image:
                rental.generate_qr_code()
                rental.save(update_fields=['qr_code_image'])
                count += 1
                tenant_name = rental.tenant.name if rental.tenant else 'No tenant'
                self.stdout.write(f'Generated QR code for rental: {rental.property_obj.name} - {tenant_name}')
        self.stdout.write(self.style.SUCCESS(f'Generated {count} rental QR codes'))
