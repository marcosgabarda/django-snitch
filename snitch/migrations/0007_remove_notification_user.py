# Generated by Django 4.1.7 on 2023-03-09 16:09

from django.db import migrations


class Migration(migrations.Migration):
    dependencies = [
        ("snitch", "0006_auto_20230220_0641"),
    ]

    operations = [
        migrations.RemoveField(
            model_name="notification",
            name="user",
        ),
    ]
