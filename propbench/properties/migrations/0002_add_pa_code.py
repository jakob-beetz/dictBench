# Generated migration for adding pa_code field to Property model

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('properties', '0001_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='property',
            name='pa_code',
            field=models.CharField(
                blank=True,
                help_text='Optional handcrafted PA identifier (e.g., PA001, PA002). Must be unique if provided.',
                max_length=20,
                null=True,
                unique=True,
                verbose_name='PA Code'
            ),
        ),
    ]