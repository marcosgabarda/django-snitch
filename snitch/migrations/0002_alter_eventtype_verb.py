# Generated by Django 3.2.2 on 2021-06-10 11:45

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("snitch", "0001_initial"),
    ]

    operations = [
        migrations.AlterField(
            model_name="eventtype",
            name="verb",
            field=models.CharField(choices=[], max_length=255, null=True, unique=True),
        ),
    ]