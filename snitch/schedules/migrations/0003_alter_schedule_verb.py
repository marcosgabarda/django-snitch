# Generated by Django 3.2.2 on 2021-06-10 11:45

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("schedules", "0002_auto_20191118_0940"),
    ]

    operations = [
        migrations.AlterField(
            model_name="schedule",
            name="verb",
            field=models.CharField(max_length=255, null=True, verbose_name="verb"),
        ),
    ]
