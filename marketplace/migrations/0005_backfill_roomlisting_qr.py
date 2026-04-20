from io import BytesIO

from django.conf import settings
from django.core.files.base import ContentFile
from django.db import migrations


def backfill_room_qr_codes(apps, schema_editor):
    try:
        import qrcode
    except ImportError:
        return

    RoomListing = apps.get_model('marketplace', 'RoomListing')
    base_url = getattr(settings, 'SITE_URL', '').rstrip('/') or 'http://127.0.0.1:8000'

    for listing in RoomListing.objects.filter(qr_code_image__isnull=True).iterator():
        url = f"{base_url}/marketplace/rooms/{listing.pk}/"
        qr = qrcode.QRCode(
            version=1,
            error_correction=qrcode.constants.ERROR_CORRECT_M,
            box_size=10,
            border=4,
        )
        qr.add_data(url)
        qr.make(fit=True)
        img = qr.make_image(fill_color='black', back_color='white')

        buffer = BytesIO()
        img.save(buffer, format='PNG')
        listing.qr_code_image.save(
            f'room_{listing.pk}.png',
            ContentFile(buffer.getvalue()),
            save=False,
        )
        listing.save(update_fields=['qr_code_image'])


def reverse_noop(apps, schema_editor):
    return


class Migration(migrations.Migration):

    dependencies = [
        ('marketplace', '0004_roomlisting_qr_code_image'),
    ]

    operations = [
        migrations.RunPython(backfill_room_qr_codes, reverse_noop),
    ]
