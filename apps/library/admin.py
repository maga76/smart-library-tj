from django.contrib import admin
from .models import AcademicYear, Classroom, StudentEnrollment, TeacherClassAssignment


@admin.register(AcademicYear)
class AcademicYearAdmin(admin.ModelAdmin):
    list_display = ['name', 'start_date', 'end_date', 'is_current']
    list_filter = ['is_current']


@admin.register(Classroom)
class ClassroomAdmin(admin.ModelAdmin):
    list_display = ['name', 'school', 'grade', 'academic_year']
    list_filter = ['school', 'grade', 'academic_year']


@admin.register(StudentEnrollment)
class StudentEnrollmentAdmin(admin.ModelAdmin):
    list_display = ['student', 'classroom', 'academic_year', 'is_active']
    list_filter = ['classroom', 'academic_year', 'is_active']


@admin.register(TeacherClassAssignment)
class TeacherClassAssignmentAdmin(admin.ModelAdmin):
    list_display = ['teacher', 'classroom', 'academic_year', 'is_class_teacher']
    list_filter = ['academic_year', 'is_class_teacher']
