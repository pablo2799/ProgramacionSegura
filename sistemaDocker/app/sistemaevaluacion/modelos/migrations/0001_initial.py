# Generated by Django 3.2.13 on 2022-06-19 20:10

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    initial = True

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='Alumnos',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('usuario', models.CharField(max_length=50)),
                ('password', models.CharField(max_length=255)),
                ('matricula', models.CharField(max_length=9)),
                ('carrera', models.CharField(max_length=40)),
                ('correo', models.CharField(max_length=30)),
                ('chatId', models.CharField(max_length=9)),
                ('tokenId', models.CharField(max_length=46)),
                ('token', models.CharField(max_length=4)),
                ('vidaToken', models.DateTimeField()),
                ('salt', models.CharField(default='0', max_length=16)),
                ('tipouser', models.CharField(default='a', max_length=1)),
            ],
        ),
        migrations.CreateModel(
            name='Ejerciciosmaestros',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('titulo', models.CharField(max_length=20)),
                ('descripcion', models.CharField(blank=True, max_length=255, null=True)),
                ('entradaPrueba', models.CharField(max_length=100)),
                ('salidaEsperada', models.CharField(blank=True, max_length=100, null=True)),
                ('scriptInicial', models.FileField(upload_to='scripts-inicializacion')),
                ('scriptComprobacionEF', models.FileField(upload_to='scripts-comprobacionEF')),
                ('scriptComprobacionP', models.FileField(upload_to='scripts-comprobacionP')),
            ],
        ),
        migrations.CreateModel(
            name='Maestros',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('usuario', models.CharField(max_length=50)),
                ('password', models.CharField(max_length=255)),
                ('nopersonal', models.CharField(max_length=5)),
                ('correo', models.CharField(max_length=30)),
                ('chatId', models.CharField(max_length=9)),
                ('tokenId', models.CharField(max_length=46)),
                ('token', models.CharField(max_length=4)),
                ('vidaToken', models.DateTimeField()),
                ('salt', models.CharField(default='0', max_length=16)),
                ('tipouser', models.CharField(default='m', max_length=1)),
            ],
        ),
        migrations.CreateModel(
            name='Peticion',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('ip', models.GenericIPAddressField(unique=True)),
                ('intentos', models.IntegerField(default=1)),
                ('timestamp', models.DateTimeField()),
            ],
        ),
        migrations.CreateModel(
            name='Ejerciciosalumnos',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('scriptEstudiante', models.FileField(upload_to='scripts-estudiantes')),
                ('resultadoFinal', models.CharField(default='NULL', max_length=10)),
                ('resultadoParametros', models.CharField(default='NULL', max_length=10)),
                ('alumno', models.ForeignKey(blank=True, max_length=50, null=True, on_delete=django.db.models.deletion.SET_NULL, to='modelos.alumnos')),
                ('ejercicio', models.ForeignKey(blank=True, max_length=20, null=True, on_delete=django.db.models.deletion.SET_NULL, to='modelos.ejerciciosmaestros')),
            ],
        ),
    ]