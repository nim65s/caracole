# Generated by Django 2.0.7 on 2018-07-23 21:50

import django.core.validators
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('videgrenier', '0001_initial'),
    ]

    operations = [
        migrations.AlterField(
            model_name='reservation',
            name='phone_number',
            field=models.CharField(
                blank=True,
                max_length=16,
                validators=[django.core.validators.RegexValidator(regex='^[+0]\\d{9,15}$')],
                verbose_name='téléphone'),
        ),
    ]
