# Generated by Django 3.2.13 on 2022-06-11 16:42

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('modelos', '0001_initial'),
    ]

    operations = [
        migrations.RenameField(
            model_name='maestros',
            old_name='contrasena',
            new_name='password',
        ),
        migrations.RenameField(
            model_name='maestros',
            old_name='maestro',
            new_name='usuario',
        ),
        migrations.AddField(
            model_name='alumnos',
            name='tipouser',
            field=models.CharField(default='a', max_length=1),
        ),
        migrations.AddField(
            model_name='maestros',
            name='tipouser',
            field=models.CharField(default='m', max_length=1),
        ),
    ]
