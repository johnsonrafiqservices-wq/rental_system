from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('marketplace', '0003_roomlisting_currency'),
    ]

    operations = [
        migrations.AddField(
            model_name='roomlisting',
            name='qr_code_image',
            field=models.ImageField(blank=True, null=True, upload_to='qr_codes/marketplace/rooms/'),
        ),
    ]
