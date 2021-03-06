# -*- coding: utf-8 -*-
# Generated by Django 1.9.5 on 2016-04-24 17:39
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('nasa', '0003_auto_20160423_2147'),
    ]

    operations = [
        migrations.AlterField(
            model_name='discretizeddatapoint',
            name='latitude',
            field=models.DecimalField(blank=True, db_index=True, decimal_places=10, max_digits=15, null=True),
        ),
        migrations.AlterField(
            model_name='discretizeddatapoint',
            name='longitude',
            field=models.DecimalField(blank=True, db_index=True, decimal_places=10, max_digits=15, null=True),
        ),
        migrations.AlterField(
            model_name='discretizeddatapoint',
            name='type',
            field=models.CharField(blank=True, db_index=True, max_length=300, null=True),
        ),
    ]
