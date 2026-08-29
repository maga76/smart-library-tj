from django.db import models
from django.utils.translation import get_language


def _localize_name(obj, fallback='name_ru'):
    lang = get_language()
    if lang == 'tg':
        return obj.name_tj
    return obj.name_ru


def _other_name(obj):
    lang = get_language()
    if lang == 'tg':
        return obj.name_ru
    return obj.name_tj


class Region(models.Model):
    name_tj = models.CharField(max_length=200)
    name_ru = models.CharField(max_length=200)
    code = models.CharField(max_length=20, unique=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = 'Region'
        verbose_name_plural = 'Regions'
        ordering = ['name_ru']

    @property
    def name(self):
        return _localize_name(self)

    @property
    def name_other(self):
        return _other_name(self)

    def __str__(self):
        return self.name_ru


class District(models.Model):
    region = models.ForeignKey(Region, on_delete=models.CASCADE, related_name='districts')
    name_tj = models.CharField(max_length=200)
    name_ru = models.CharField(max_length=200)
    code = models.CharField(max_length=20, unique=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = 'District'
        verbose_name_plural = 'Districts'
        ordering = ['name_ru']

    @property
    def name(self):
        return _localize_name(self)

    @property
    def name_other(self):
        return _other_name(self)

    def __str__(self):
        return f'{self.name_ru} ({self.region.name_ru})'


class Jamoat(models.Model):
    district = models.ForeignKey(District, on_delete=models.CASCADE, related_name='jamoats')
    name_tj = models.CharField(max_length=200)
    name_ru = models.CharField(max_length=200)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = 'Jamoat'
        verbose_name_plural = 'Jamoats'
        ordering = ['name_ru']

    @property
    def name(self):
        return _localize_name(self)

    @property
    def name_other(self):
        return _other_name(self)

    def __str__(self):
        return f'{self.name_ru} ({self.district.name_ru})'
