# Generated by Django 3.2.6 on 2024-05-25 01:51

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("background_task", "0002_auto_20170927_1109"),
    ]

    operations = [
        migrations.AddField(
            model_name="completedtask",
            name="worker",
            field=models.CharField(
                blank=True, db_index=True, max_length=128, null=True
            ),
        ),
        migrations.AddField(
            model_name="task",
            name="worker",
            field=models.CharField(
                blank=True, db_index=True, max_length=128, null=True
            ),
        ),
        migrations.AlterField(
            model_name="completedtask",
            name="id",
            field=models.BigAutoField(
                auto_created=True,
                primary_key=True,
                serialize=False,
                verbose_name="ID",
            ),
        ),
        migrations.AlterField(
            model_name="task",
            name="id",
            field=models.BigAutoField(
                auto_created=True,
                primary_key=True,
                serialize=False,
                verbose_name="ID",
            ),
        ),
    ]
