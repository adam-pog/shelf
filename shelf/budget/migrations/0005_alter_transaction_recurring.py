# Generated by Django 3.2.7 on 2021-09-06 21:57

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('budget', '0004_auto_20210906_2149'),
    ]

    operations = [
        migrations.AlterField(
            model_name='transaction',
            name='recurring',
            field=models.BooleanField(default=False),
        ),
    ]
