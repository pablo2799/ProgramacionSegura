# Generated by Django 3.2.13 on 2022-06-21 00:00

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('modelos', '0001_initial'),
    ]

    operations = [
        migrations.AlterField(
            model_name='ejerciciosmaestros',
            name='titulo',
            field=models.CharField(max_length=50),
        ),
    ]