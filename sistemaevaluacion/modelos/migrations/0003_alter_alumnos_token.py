# Generated by Django 3.2.13 on 2022-06-21 23:39

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('modelos', '0002_alter_ejerciciosmaestros_titulo'),
    ]

    operations = [
        migrations.AlterField(
            model_name='alumnos',
            name='token',
            field=models.CharField(max_length=6),
        ),
    ]
