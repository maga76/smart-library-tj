from django.test import TestCase, Client
from django.urls import reverse
from accounts.models import User
from geography.models import Region, District, Jamoat
from schools.models import School


class RoleAccessTests(TestCase):
    def setUp(self):
        self.client = Client()
        self.region = Region.objects.create(name_tj='Душанбе', name_ru='Душанбе', code='DUSH')
        self.district = District.objects.create(region=self.region, name_tj='Сино', name_ru='Сино', code='SINO')
        self.jamoat = Jamoat.objects.create(district=self.district, name_tj='Ҷамоат', name_ru='Джамоат')
        self.school = School.objects.create(
            name='Школа №15', school_number='15',
            region=self.region, district=self.district, jamoat=self.jamoat
        )

        self.super_admin = User.objects.create_user(username='super_admin', password='password123', role=User.Role.SUPER_ADMIN)
        self.librarian = User.objects.create_user(username='librarian', password='password123', role=User.Role.LIBRARIAN, school=self.school)
        self.teacher = User.objects.create_user(username='teacher', password='password123', role=User.Role.CLASS_TEACHER, school=self.school)
        self.student = User.objects.create_user(username='student', password='password123', role=User.Role.STUDENT, school=self.school)

    def test_dashboard_url_property(self):
        self.assertEqual(self.super_admin.dashboard_url, '/dashboard/super-admin/')
        self.assertEqual(self.librarian.dashboard_url, '/dashboard/librarian/')
        self.assertEqual(self.teacher.dashboard_url, '/dashboard/teacher/')
        self.assertEqual(self.student.dashboard_url, '/dashboard/student/')

    def test_role_access_restriction(self):
        # Student trying to access super admin dashboard
        self.client.login(username='student', password='password123')
        res = self.client.get('/dashboard/super-admin/')
        self.assertEqual(res.status_code, 403)

        # Teacher trying to access geography management
        self.client.login(username='teacher', password='password123')
        res = self.client.get('/geography/regions/')
        self.assertEqual(res.status_code, 403)

        # Super admin has access
        self.client.login(username='super_admin', password='password123')
        res = self.client.get('/dashboard/super-admin/')
        self.assertEqual(res.status_code, 200)
