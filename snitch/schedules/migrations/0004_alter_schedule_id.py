# Generated by Django 4.1.6 on 2023-02-02 09:09

from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("schedules", "0003_alter_schedule_verb"),
    ]

    operations = [
        migrations.AlterField(
            model_name="schedule",
            name="id",
            field=models.BigAutoField(
                auto_created=True, primary_key=True, serialize=False, verbose_name="ID"
            ),
        ),
    ]