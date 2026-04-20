# Rental Management System

A Django application for managing company and individual rentals with QR code technology for every registered property.

## Features

- **Owner Registration**: Register companies or individuals as property owners
- **Property Management**: Manage rentable properties with location details
- **Self-Calculated Property Count**: Automatically calculates the number of properties for each owner
- **QR Code Generation**: Every registered property gets a unique QR code
- **Rental Agreements**: Create and manage rental agreements between properties and tenants
- **Dashboard**: Overview of all rentals, properties, and owners
- **Filtering & Search**: Advanced filtering for owners, properties, and rentals
- **Admin Interface**: Full Django admin for managing all data

## Requirements

- Python 3.8+
- Django 4.2.20
- qrcode 7.4.2
- Pillow 10.3.0

## Installation

1. Navigate to the project directory:
```bash
cd rental_system
```

2. Install dependencies:
```bash
pip install -r requirements.txt
```

3. Run migrations (already applied, but can be re-run if needed):
```bash
python manage.py migrate
```

4. Create a superuser for admin access:
```bash
python manage.py createsuperuser
```

5. Run the development server:
```bash
python manage.py runserver
```

6. Access the application:
   - Frontend: http://127.0.0.1:8000/
   - Admin: http://127.0.0.1:8000/admin/

## Project Structure

```
rental_system/
├── rentals/                    # Main app
│   ├── models.py              # Owner, Property, QRCode, Rental models
│   ├── views.py               # All views
│   ├── forms.py               # Owner, Property, Rental forms
│   ├── admin.py               # Admin configuration
│   ├── urls.py                # App URLs
│   └── templates/rentals/     # HTML templates
│       ├── base.html
│       ├── dashboard.html
│       ├── owner_list.html
│       ├── owner_form.html
│       ├── owner_detail.html
│       ├── property_list.html
│       ├── property_form.html
│       ├── property_detail.html
│       ├── rental_list.html
│       ├── rental_form.html
│       └── rental_detail.html
├── rental_system/             # Project settings
│   ├── settings.py
│   └── urls.py
├── media/                     # QR code images (auto-created)
└── requirements.txt
```

## Models

### Owner
- Can be a Company or Individual
- Fields: name, email, phone, address, city, country
- Self-calculated `property_count` property

### Property
- Linked to an Owner
- Property types: Residential, Commercial, Industrial, Land, Parking, Storage
- Location fields: address, city, state, postal code, country, latitude, longitude
- Property details: area, rooms, bathrooms, floor number
- Financial: base rent, currency
- Status: active, available

### QRCode
- Auto-generated for each property
- Contains property details encoded in QR
- Unique identifier for tracking

### Rental
- Links Property to Tenant (Owner)
- Status: Pending, Active, Expired, Terminated
- Rental period: start date, end date
- Financial: monthly rent, currency, deposit amount
- Terms and notes

## URL Patterns

- `/` - Dashboard
- `/owners/` - List all owners
- `/owners/create/` - Register new owner
- `/owners/<uuid:pk>/` - Owner details
- `/properties/` - List all properties
- `/properties/create/` - Add new property (auto-generates QR code)
- `/properties/<uuid:pk>/` - Property details with QR code
- `/rentals/` - List all rentals
- `/rentals/create/` - Create rental agreement
- `/rentals/<uuid:pk>/` - Rental details
- `/admin/` - Django admin interface

## QR Code Functionality

QR codes are automatically generated when a property is created. The QR code contains:
- Property ID
- Property name
- Address
- Unique identifier

Note: QR code generation requires the `qrcode` package. If not installed, properties can still be created without QR codes. Install qrcode to enable full functionality:
```bash
pip install qrcode
```

## Admin Access

Access the Django admin panel at `/admin/` to:
- Manage Owners, Properties, QR Codes, and Rentals
- View detailed information
- Bulk edit records
- Export data

## Development Notes

- Timezone set to Africa/Kampala
- SQLite database (can be changed to PostgreSQL/MySQL in settings.py)
- Media files (QR codes) served in development mode
- Bootstrap 5 for responsive UI
- Bootstrap Icons for iconography

## License

This project is for demonstration purposes.
