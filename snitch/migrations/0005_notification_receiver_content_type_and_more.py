# Generated by Django 4.1.6 on 2023-02-20 12:40

import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models

import snitch.helpers


class Migration(migrations.Migration):
    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ("contenttypes", "0002_remove_content_type_name"),
        ("snitch", "0004_alter_event_id_alter_eventtype_id_and_more"),
    ]

    operations = [
        migrations.AddField(
            model_name="notification",
            name="receiver_content_type",
            field=models.ForeignKey(
                limit_choices_to=snitch.helpers.receiver_content_type_choices,
                null=True,
                on_delete=django.db.models.deletion.CASCADE,
                to="contenttypes.contenttype",
                verbose_name="receiver content type",
            ),
        ),
        migrations.AddField(
            model_name="notification",
            name="receiver_id",
            field=models.PositiveIntegerField(null=True, verbose_name="receiver id"),
        ),
        migrations.AlterField(
            model_name="notification",
            name="user",
            field=models.ForeignKey(
                blank=True,
                help_text="User owner of the notification. It can be the same as de receiver.",
                null=True,
                on_delete=django.db.models.deletion.CASCADE,
                related_name="notifications",
                to=settings.AUTH_USER_MODEL,
            ),
        ),
    ]