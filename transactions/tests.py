import datetime
from django.test import TestCase, Client
from accounts.models import User
from geography.models import Region, District, Jamoat
from schools.models import School
from library.models import AcademicYear, Classroom, StudentEnrollment, TeacherClassAssignment, Book, BookCopy
from transactions.models import BookTransaction


class BookMovementLifecycleTests(TestCase):
    def setUp(self):
        self.client = Client()
        self.year = AcademicYear.objects.create(
            name='2026-2027', start_date=datetime.date(2026, 9, 1), end_date=datetime.date(2027, 5, 25), is_current=True
        )
        self.region = Region.objects.create(name_tj='Душанбе', name_ru='Душанбе', code='DUSH')
        self.district = District.objects.create(region=self.region, name_tj='Сино', name_ru='Сино', code='SINO')
        self.jamoat = Jamoat.objects.create(district=self.district, name_tj='Ҷамоат', name_ru='Джамоат')
        self.school = School.objects.create(
            name='Школа №15', school_number='15',
            region=self.region, district=self.district, jamoat=self.jamoat
        )

        self.librarian = User.objects.create_user(username='librarian', password='password123', role=User.Role.LIBRARIAN, school=self.school)
        self.teacher = User.objects.create_user(username='teacher', password='password123', role=User.Role.CLASS_TEACHER, school=self.school)
        self.student = User.objects.create_user(username='student', password='password123', role=User.Role.STUDENT, school=self.school)

        self.classroom = Classroom.objects.create(school=self.school, name='10-А', grade=10, academic_year=self.year)
        TeacherClassAssignment.objects.create(teacher=self.teacher, classroom=self.classroom, academic_year=self.year, is_class_teacher=True)
        StudentEnrollment.objects.create(student=self.student, classroom=self.classroom, academic_year=self.year, is_active=True)

        self.book = Book.objects.create(title='Алгебра 10', author='Алимов', subject='Алгебра', grade=10, language='tj', isbn='111-222')
        self.copy = BookCopy.objects.create(
            book=self.book, inventory_number='TJ-S015-001', barcode='BC015001',
            school=self.school, status=BookCopy.Status.AT_LIBRARY
        )

    def test_full_movement_chain(self):
        # 1. Librarian issues to Teacher
        self.client.login(username='librarian', password='password123')
        res = self.client.post('/transactions/issue-teacher/', {
            'book_copies': [self.copy.pk],
            'teacher': self.teacher.pk,
            'note': 'Issue to 10-A class teacher'
        })
        self.assertEqual(res.status_code, 302)

        self.copy.refresh_from_db()
        self.assertEqual(self.copy.status, BookCopy.Status.ISSUED_TO_TEACHER)
        self.assertTrue(BookTransaction.objects.filter(transaction_type='LIBRARIAN_TO_TEACHER', to_user=self.teacher).exists())

        # 2. Teacher issues to Student
        self.client.login(username='teacher', password='password123')
        res = self.client.post('/transactions/issue-student/', {
            'book_copy': self.copy.pk,
            'student': self.student.pk,
            'note': 'Issued for semester'
        })
        self.assertEqual(res.status_code, 302)

        self.copy.refresh_from_db()
        self.assertEqual(self.copy.status, BookCopy.Status.ISSUED_TO_STUDENT)
        self.assertTrue(BookTransaction.objects.filter(transaction_type='TEACHER_TO_STUDENT', to_user=self.student).exists())

        # 3. Student returns to Teacher
        res = self.client.post('/transactions/return-student/', {
            'book_copy': self.copy.pk,
            'note': 'Good condition'
        })
        self.assertEqual(res.status_code, 302)

        self.copy.refresh_from_db()
        self.assertEqual(self.copy.status, BookCopy.Status.ISSUED_TO_TEACHER)
        self.assertTrue(BookTransaction.objects.filter(transaction_type='STUDENT_RETURN', to_user=self.teacher).exists())

        # 4. Teacher returns to Librarian
        self.client.login(username='librarian', password='password123')
        res = self.client.post('/transactions/return-teacher/', {
            'book_copies': [self.copy.pk],
        })
        self.assertEqual(res.status_code, 302)

        self.copy.refresh_from_db()
        self.assertEqual(self.copy.status, BookCopy.Status.AT_LIBRARY)
        self.assertTrue(BookTransaction.objects.filter(transaction_type='TEACHER_RETURN', to_user=self.librarian).exists())
