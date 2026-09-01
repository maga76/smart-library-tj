from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.core.paginator import Paginator
from django.db.models import Q
from django.utils.translation import gettext_lazy as _
from django.views import View
from core.mixins import RoleRequiredMixin
from .models import Region, District, Jamoat
from audit.utils import log_audit


# ==============================
# REGIONS
# ==============================

class RegionListView(RoleRequiredMixin, View):
    allowed_roles = ['SUPER_ADMIN']

    def get(self, request):
        regions = Region.objects.all().order_by('name_ru')
        search = request.GET.get('search', '').strip()
        if search:
            regions = regions.filter(
                Q(name_ru__icontains=search) |
                Q(name_tj__icontains=search) |
                Q(code__icontains=search)
            )

        paginator = Paginator(regions, 20)
        page_obj = paginator.get_page(request.GET.get('page'))
        return render(request, 'geography/region_list.html', {
            'regions': page_obj,
            'page_obj': page_obj,
            'search': search,
        })


class RegionCreateView(RoleRequiredMixin, View):
    allowed_roles = ['SUPER_ADMIN']

    def get(self, request):
        return render(request, 'geography/region_form.html', {'title': _('Create Region')})

    def post(self, request):
        name_tj = request.POST.get('name_tj', '').strip()
        name_ru = request.POST.get('name_ru', '').strip()
        code = request.POST.get('code', '').strip().upper()
        if not name_tj or not name_ru or not code:
            messages.error(request, _('All required fields must be filled in.'))
            return render(request, 'geography/region_form.html', {'title': _('Create Region')})

        region = Region.objects.create(name_tj=name_tj, name_ru=name_ru, code=code)
        log_audit(request.user, 'REGION_CREATE', 'Region', region.pk, f'Created region {region.name_ru} ({region.code})')
        messages.success(request, _('Region "%(name)s" has been successfully created.') % {'name': region.name_ru})
        return redirect('geography:region_list')


class RegionEditView(RoleRequiredMixin, View):
    allowed_roles = ['SUPER_ADMIN']

    def get(self, request, pk):
        region = get_object_or_404(Region, pk=pk)
        return render(request, 'geography/region_form.html', {'title': _('Edit Region'), 'region': region})

    def post(self, request, pk):
        region = get_object_or_404(Region, pk=pk)
        region.name_tj = request.POST.get('name_tj', region.name_tj).strip()
        region.name_ru = request.POST.get('name_ru', region.name_ru).strip()
        region.code = request.POST.get('code', region.code).strip().upper()
        region.is_active = 'is_active' in request.POST
        region.save()
        log_audit(request.user, 'REGION_UPDATE', 'Region', region.pk, f'Updated region {region.name_ru}')
        messages.success(request, _('Region "%(name)s" has been successfully updated.') % {'name': region.name_ru})
        return redirect('geography:region_list')


class RegionToggleActiveView(RoleRequiredMixin, View):
    allowed_roles = ['SUPER_ADMIN']

    def post(self, request, pk):
        region = get_object_or_404(Region, pk=pk)
        region.is_active = not region.is_active
        region.save()
        status_text = _('activated') if region.is_active else _('deactivated')
        log_audit(request.user, 'REGION_TOGGLE_ACTIVE', 'Region', region.pk, f'Region {region.name_ru} is now {status_text}')
        messages.success(request, _('Region "%(name)s" %(status)s.') % {'name': region.name_ru, 'status': status_text})
        return redirect('geography:region_list')

    def get(self, request, pk):
        return redirect('geography:region_list')


# ==============================
# DISTRICTS
# ==============================

class DistrictListView(RoleRequiredMixin, View):
    allowed_roles = ['SUPER_ADMIN']

    def get(self, request):
        districts = District.objects.select_related('region').all().order_by('region__name_ru', 'name_ru')
        region_filter = request.GET.get('region', '')
        search = request.GET.get('search', '').strip()

        if region_filter:
            districts = districts.filter(region_id=region_filter)
        if search:
            districts = districts.filter(
                Q(name_ru__icontains=search) |
                Q(name_tj__icontains=search) |
                Q(code__icontains=search) |
                Q(region__name_ru__icontains=search)
            )

        paginator = Paginator(districts, 25)
        page_obj = paginator.get_page(request.GET.get('page'))
        regions = Region.objects.filter(is_active=True)
        return render(request, 'geography/district_list.html', {
            'districts': page_obj,
            'page_obj': page_obj,
            'regions': regions,
            'region_filter': region_filter,
            'search': search,
        })


class DistrictCreateView(RoleRequiredMixin, View):
    allowed_roles = ['SUPER_ADMIN']

    def get(self, request):
        regions = Region.objects.filter(is_active=True)
        return render(request, 'geography/district_form.html', {'title': _('Create District'), 'regions': regions})

    def post(self, request):
        region_id = request.POST.get('region')
        name_tj = request.POST.get('name_tj', '').strip()
        name_ru = request.POST.get('name_ru', '').strip()
        code = request.POST.get('code', '').strip().upper()
        if not region_id or not name_tj or not name_ru or not code:
            messages.error(request, _('Fill in all required fields.'))
            regions = Region.objects.filter(is_active=True)
            return render(request, 'geography/district_form.html', {'title': _('Create District'), 'regions': regions})

        district = District.objects.create(
            region_id=region_id,
            name_tj=name_tj,
            name_ru=name_ru,
            code=code
        )
        log_audit(request.user, 'DISTRICT_CREATE', 'District', district.pk, f'Created district {district.name_ru} in {district.region.name_ru}')
        messages.success(request, _('District "%(name)s" has been successfully created.') % {'name': district.name_ru})
        return redirect('geography:district_list')


class DistrictEditView(RoleRequiredMixin, View):
    allowed_roles = ['SUPER_ADMIN']

    def get(self, request, pk):
        district = get_object_or_404(District, pk=pk)
        regions = Region.objects.filter(is_active=True)
        return render(request, 'geography/district_form.html', {
            'title': _('Edit District'),
            'district': district,
            'regions': regions,
        })

    def post(self, request, pk):
        district = get_object_or_404(District, pk=pk)
        district.region_id = request.POST.get('region', district.region_id)
        district.name_tj = request.POST.get('name_tj', district.name_tj).strip()
        district.name_ru = request.POST.get('name_ru', district.name_ru).strip()
        district.code = request.POST.get('code', district.code).strip().upper()
        district.is_active = 'is_active' in request.POST
        district.save()
        log_audit(request.user, 'DISTRICT_UPDATE', 'District', district.pk, f'Updated district {district.name_ru}')
        messages.success(request, _('District "%(name)s" has been successfully updated.') % {'name': district.name_ru})
        return redirect('geography:district_list')


class DistrictToggleActiveView(RoleRequiredMixin, View):
    allowed_roles = ['SUPER_ADMIN']

    def post(self, request, pk):
        district = get_object_or_404(District, pk=pk)
        district.is_active = not district.is_active
        district.save()
        status_text = _('activated') if district.is_active else _('deactivated')
        log_audit(request.user, 'DISTRICT_TOGGLE_ACTIVE', 'District', district.pk, f'District {district.name_ru} is now {status_text}')
        messages.success(request, _('District "%(name)s" %(status)s.') % {'name': district.name_ru, 'status': status_text})
        return redirect('geography:district_list')

    def get(self, request, pk):
        return redirect('geography:district_list')


# ==============================
# JAMOATS
# ==============================

class JamoatListView(RoleRequiredMixin, View):
    allowed_roles = ['SUPER_ADMIN']

    def get(self, request):
        jamoats = Jamoat.objects.select_related('district', 'district__region').all().order_by('district__name_ru', 'name_ru')
        district_filter = request.GET.get('district', '')
        search = request.GET.get('search', '').strip()

        if district_filter:
            jamoats = jamoats.filter(district_id=district_filter)
        if search:
            jamoats = jamoats.filter(
                Q(name_ru__icontains=search) |
                Q(name_tj__icontains=search) |
                Q(district__name_ru__icontains=search)
            )

        paginator = Paginator(jamoats, 25)
        page_obj = paginator.get_page(request.GET.get('page'))
        districts = District.objects.filter(is_active=True).select_related('region')
        return render(request, 'geography/jamoat_list.html', {
            'jamoats': page_obj,
            'page_obj': page_obj,
            'districts': districts,
            'district_filter': district_filter,
            'search': search,
        })


class JamoatCreateView(RoleRequiredMixin, View):
    allowed_roles = ['SUPER_ADMIN']

    def get(self, request):
        districts = District.objects.filter(is_active=True)
        return render(request, 'geography/jamoat_form.html', {'title': _('Create Jamoat'), 'districts': districts})

    def post(self, request):
        district_id = request.POST.get('district')
        name_tj = request.POST.get('name_tj', '').strip()
        name_ru = request.POST.get('name_ru', '').strip()
        if not district_id or not name_tj or not name_ru:
            messages.error(request, _('Fill in all required fields.'))
            districts = District.objects.filter(is_active=True)
            return render(request, 'geography/jamoat_form.html', {'title': _('Create Jamoat'), 'districts': districts})

        jamoat = Jamoat.objects.create(
            district_id=district_id,
            name_tj=name_tj,
            name_ru=name_ru
        )
        log_audit(request.user, 'JAMOAT_CREATE', 'Jamoat', jamoat.pk, f'Created jamoat {jamoat.name_ru} in {jamoat.district.name_ru}')
        messages.success(request, _('Jamoat "%(name)s" has been successfully created.') % {'name': jamoat.name_ru})
        return redirect('geography:jamoat_list')


class JamoatEditView(RoleRequiredMixin, View):
    allowed_roles = ['SUPER_ADMIN']

    def get(self, request, pk):
        jamoat = get_object_or_404(Jamoat, pk=pk)
        districts = District.objects.filter(is_active=True)
        return render(request, 'geography/jamoat_form.html', {
            'title': _('Edit Jamoat'),
            'jamoat': jamoat,
            'districts': districts,
        })

    def post(self, request, pk):
        jamoat = get_object_or_404(Jamoat, pk=pk)
        jamoat.district_id = request.POST.get('district', jamoat.district_id)
        jamoat.name_tj = request.POST.get('name_tj', jamoat.name_tj).strip()
        jamoat.name_ru = request.POST.get('name_ru', jamoat.name_ru).strip()
        jamoat.is_active = 'is_active' in request.POST
        jamoat.save()
        log_audit(request.user, 'JAMOAT_UPDATE', 'Jamoat', jamoat.pk, f'Updated jamoat {jamoat.name_ru}')
        messages.success(request, _('Jamoat "%(name)s" has been successfully updated.') % {'name': jamoat.name_ru})
        return redirect('geography:jamoat_list')


class JamoatToggleActiveView(RoleRequiredMixin, View):
    allowed_roles = ['SUPER_ADMIN']

    def post(self, request, pk):
        jamoat = get_object_or_404(Jamoat, pk=pk)
        jamoat.is_active = not jamoat.is_active
        jamoat.save()
        status_text = _('activated') if jamoat.is_active else _('deactivated')
        log_audit(request.user, 'JAMOAT_TOGGLE_ACTIVE', 'Jamoat', jamoat.pk, f'Jamoat {jamoat.name_ru} is now {status_text}')
        messages.success(request, _('Jamoat "%(name)s" %(status)s.') % {'name': jamoat.name_ru, 'status': status_text})
        return redirect('geography:jamoat_list')

    def get(self, request, pk):
        return redirect('geography:jamoat_list')
