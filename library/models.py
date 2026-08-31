from django.db import models
from django.utils.translation import gettext_lazy as _


class AcademicYear(models.Model):
    name = models.CharField(max_length=20, unique=True)
    start_date = models.DateField()
    end_date = models.DateField()
    is_current = models.BooleanField(default=False)

    class Meta:
        verbose_name = 'Academic Year'
        verbose_name_plural = 'Academic Years'
        ordering = ['-start_date']

    def __str__(self):
        return self.name

    def save(self, *args, **kwargs):
        if self.is_current:
            AcademicYear.objects.filter(is_current=True).exclude(pk=self.pk).update(is_current=False)
        super().save(*args, **kwargs)


class Classroom(models.Model):
    GRADE_CHOICES = [(i, str(i)) for i in range(1, 12)]
    school = models.ForeignKey('schools.School', on_delete=models.CASCADE, related_name='classrooms')
    name = models.CharField(max_length=20)
    grade = models.PositiveSmallIntegerField(choices=GRADE_CHOICES)
    academic_year = models.ForeignKey(AcademicYear, on_delete=models.CASCADE, related_name='classrooms')

    class Meta:
        verbose_name = 'Classroom'
        verbose_name_plural = 'Classrooms'
        unique_together = ['school', 'name', 'academic_year']
        ordering = ['grade', 'name']

    def __str__(self):
        return f'{self.name} (Grade {self.grade})'


class StudentEnrollment(models.Model):
    student = models.ForeignKey('accounts.User', on_delete=models.CASCADE, related_name='enrollments')
    classroom = models.ForeignKey(Classroom, on_delete=models.CASCADE, related_name='enrollments')
    academic_year = models.ForeignKey(AcademicYear, on_delete=models.CASCADE, related_name='enrollments')
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = 'Student Enrollment'
        verbose_name_plural = 'Student Enrollments'
        unique_together = ['student', 'academic_year']

    def __str__(self):
        return f'{self.student.get_full_name()} - {self.classroom.name}'


class TeacherClassAssignment(models.Model):
    teacher = models.ForeignKey('accounts.User', on_delete=models.CASCADE, related_name='class_assignments')
    classroom = models.ForeignKey(Classroom, on_delete=models.CASCADE, related_name='teacher_assignments')
    academic_year = models.ForeignKey(AcademicYear, on_delete=models.CASCADE, related_name='teacher_assignments')
    is_class_teacher = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = 'Teacher Class Assignment'
        verbose_name_plural = 'Teacher Class Assignments'
        unique_together = ['teacher', 'classroom', 'academic_year']

    def __str__(self):
        role = 'Class Teacher' if self.is_class_teacher else 'Subject Teacher'
        return f'{self.teacher.get_full_name()} - {self.classroom.name} ({role})'


class Book(models.Model):
    GRADE_CHOICES = [(i, str(i)) for i in range(1, 12)]
    LANGUAGE_CHOICES = [
        ('tj', _('Tajik')),
        ('ru', _('Russian')),
    ]

    title = models.CharField(max_length=500)
    author = models.CharField(max_length=300)
    subject = models.CharField(max_length=200)
    grade = models.PositiveSmallIntegerField(choices=GRADE_CHOICES)
    language = models.CharField(max_length=5, choices=LANGUAGE_CHOICES, default='tj')
    isbn = models.CharField(max_length=20, blank=True)
    publisher = models.CharField(max_length=300, blank=True)
    publication_year = models.PositiveIntegerField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = 'Book'
        verbose_name_plural = 'Books'
        ordering = ['title']

    def __str__(self):
        return f'{self.title} ({self.author})'


class BookCopy(models.Model):
    class Status(models.TextChoices):
        AVAILABLE = 'AVAILABLE', _('Available')
        AT_LIBRARY = 'AT_LIBRARY', _('At Library')
        ISSUED_TO_TEACHER = 'ISSUED_TO_TEACHER', _('Issued to Teacher')
        ISSUED_TO_STUDENT = 'ISSUED_TO_STUDENT', _('Issued to Student')
        RETURNED = 'RETURNED', _('Returned')
        LOST = 'LOST', _('Lost')
        DAMAGED = 'DAMAGED', _('Damaged')
        WRITTEN_OFF = 'WRITTEN_OFF', _('Written Off')

    book = models.ForeignKey(Book, on_delete=models.CASCADE, related_name='copies')
    inventory_number = models.CharField(max_length=50, unique=True)
    barcode = models.CharField(max_length=100, unique=True)
    qr_code = models.CharField(max_length=200, blank=True)
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.AVAILABLE)
    school = models.ForeignKey('schools.School', on_delete=models.CASCADE, related_name='book_copies')
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = 'Book Copy'
        verbose_name_plural = 'Book Copies'
        ordering = ['inventory_number']

    def __str__(self):
        return f'{self.book.title} - {self.inventory_number}'


class BookRequest(models.Model):
    class Status(models.TextChoices):
        PENDING = 'PENDING', _('Pending')
        APPROVED = 'APPROVED', _('Approved')
        REJECTED = 'REJECTED', _('Rejected')
        FULFILLED = 'FULFILLED', _('Fulfilled')

    school = models.ForeignKey('schools.School', on_delete=models.CASCADE, related_name='book_requests')
    book = models.ForeignKey(Book, on_delete=models.CASCADE, related_name='requests')
    requested_quantity = models.PositiveIntegerField()
    available_quantity = models.PositiveIntegerField(default=0)
    reason = models.TextField(blank=True)
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.PENDING)
    created_by = models.ForeignKey('accounts.User', on_delete=models.SET_NULL, null=True, related_name='created_requests')
    created_at = models.DateTimeField(auto_now_add=True)
    approved_by = models.ForeignKey('accounts.User', on_delete=models.SET_NULL, null=True, blank=True, related_name='approved_requests')
    approved_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        verbose_name = 'Book Request'
        verbose_name_plural = 'Book Requests'
        ordering = ['-created_at']

    def __str__(self):
        return f'{self.book.title} - {self.school.name} ({self.get_status_display()})'


class StudentBookRequest(models.Model):
    class Status(models.TextChoices):
        PENDING = 'PENDING', _('Pending')
        REVIEWED = 'REVIEWED', _('Reviewed')
        APPROVED = 'APPROVED', _('Approved')
        REJECTED = 'REJECTED', _('Rejected')

    student = models.ForeignKey('accounts.User', on_delete=models.CASCADE, related_name='student_book_requests')
    school = models.ForeignKey('schools.School', on_delete=models.CASCADE, related_name='student_book_requests')
    book = models.ForeignKey(Book, on_delete=models.CASCADE, related_name='student_requests')
    reason = models.TextField(blank=True)
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.PENDING)
    created_at = models.DateTimeField(auto_now_add=True)
    reviewed_by = models.ForeignKey('accounts.User', on_delete=models.SET_NULL, null=True, blank=True, related_name='reviewed_student_requests')
    reviewed_at = models.DateTimeField(null=True, blank=True)
    review_note = models.TextField(blank=True)

    class Meta:
        verbose_name = _('Student Book Request')
        verbose_name_plural = _('Student Book Requests')
        ordering = ['-created_at']

    def __str__(self):
        return f'{self.student.get_full_name()} - {self.book.title} ({self.get_status_display()})'


class BookIssue(models.Model):
    class IssueType(models.TextChoices):
        LOST = 'LOST', _('Lost')
        DAMAGED = 'DAMAGED', _('Damaged')

    class IssueStatus(models.TextChoices):
        PENDING = 'PENDING', _('Pending')
        CONFIRMED = 'CONFIRMED', _('Confirmed')
        REJECTED = 'REJECTED', _('Rejected')

    book_copy = models.ForeignKey(BookCopy, on_delete=models.CASCADE, related_name='issues')
    student = models.ForeignKey('accounts.User', on_delete=models.CASCADE, related_name='book_issues')
    issue_type = models.CharField(max_length=10, choices=IssueType.choices)
    description = models.TextField(blank=True)
    reported_by = models.ForeignKey('accounts.User', on_delete=models.SET_NULL, null=True, related_name='reported_issues')
    reported_at = models.DateTimeField(auto_now_add=True)
    status = models.CharField(max_length=15, choices=IssueStatus.choices, default=IssueStatus.PENDING)
    confirmed_by = models.ForeignKey('accounts.User', on_delete=models.SET_NULL, null=True, blank=True, related_name='confirmed_issues')
    confirmed_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        verbose_name = 'Book Issue'
        verbose_name_plural = 'Book Issues'
        ordering = ['-reported_at']

    def __str__(self):
        return f'{self.book_copy.inventory_number} - {self.get_issue_type_display()}'
