import datetime
from django.core.management.base import BaseCommand
from apps.accounts.models import User
from apps.geography.models import Region, District, Jamoat
from apps.schools.models import School
from apps.library.models import (
    AcademicYear, Classroom, StudentEnrollment, TeacherClassAssignment,
    Book, BookCopy, BookRequest, BookIssue
)
from apps.transactions.models import BookTransaction
from apps.audit.utils import log_audit


class Command(BaseCommand):
    help = 'Populates the Smart Library TJ database with comprehensive demo and initial seed data.'

    def handle(self, *args, **options):
        self.stdout.write(self.style.NOTICE('Starting Smart Library TJ database seeding...'))

        # 1. Academic Year
        year, _ = AcademicYear.objects.get_or_create(
            name='2026-2027',
            defaults={
                'start_date': datetime.date(2026, 9, 1),
                'end_date': datetime.date(2027, 5, 25),
                'is_current': True,
            }
        )
        self.stdout.write(self.style.SUCCESS(f'Academic Year: {year.name}'))

        # 2. Geography: Regions
        reg_dushanbe, _ = Region.objects.get_or_create(
            code='DUSH',
            defaults={'name_tj': 'Шаҳри Душанбе', 'name_ru': 'город Душанбе', 'is_active': True}
        )
        reg_sughd, _ = Region.objects.get_or_create(
            code='SUGHD',
            defaults={'name_tj': 'Вилояти Суғд', 'name_ru': 'Согдийская область', 'is_active': True}
        )
        reg_khatlon, _ = Region.objects.get_or_create(
            code='KHATLON',
            defaults={'name_tj': 'Вилояти Хатлон', 'name_ru': 'Хатлонская область', 'is_active': True}
        )
        reg_gbao, _ = Region.objects.get_or_create(
            code='GBAO',
            defaults={'name_tj': 'ВМКБ', 'name_ru': 'ГБАО', 'is_active': True}
        )
        reg_rrs, _ = Region.objects.get_or_create(
            code='RRS',
            defaults={'name_tj': 'НТҶ', 'name_ru': 'РРП (Ноҳияҳои тобеи ҷумҳурӣ)', 'is_active': True}
        )

        # Districts
        dist_sino, _ = District.objects.get_or_create(
            code='SINO',
            defaults={'region': reg_dushanbe, 'name_tj': 'Ноҳияи Сино', 'name_ru': 'Район Сино', 'is_active': True}
        )
        dist_somoni, _ = District.objects.get_or_create(
            code='SOMONI',
            defaults={'region': reg_dushanbe, 'name_tj': 'Ноҳияи Исмоили Сомонӣ', 'name_ru': 'Район Исмоили Сомони', 'is_active': True}
        )
        dist_khujand, _ = District.objects.get_or_create(
            code='KHUJAND',
            defaults={'region': reg_sughd, 'name_tj': 'Шаҳри Хуҷанд', 'name_ru': 'город Худжанд', 'is_active': True}
        )

        # Jamoats
        jam_sino1, _ = Jamoat.objects.get_or_create(
            district=dist_sino,
            name_ru='Маҳаллаи 101/102 (Сино)',
            defaults={'name_tj': 'Маҳаллаи 101/102 (Сино)', 'is_active': True}
        )
        jam_somoni1, _ = Jamoat.objects.get_or_create(
            district=dist_somoni,
            name_ru='Маҳаллаи Шаҳрак (И. Сомони)',
            defaults={'name_tj': 'Маҳаллаи Шаҳрак (И. Сомонӣ)', 'is_active': True}
        )

        # 3. Schools
        school15, _ = School.objects.get_or_create(
            school_number='15',
            defaults={
                'name': 'Мактаби таҳсилоти миёнаи умумии №15',
                'region': reg_dushanbe,
                'district': dist_somoni,
                'jamoat': jam_somoni1,
                'address': 'ш. Душанбе, хиёбони Рӯдакӣ 120',
                'phone': '+992 37 221-15-15',
                'email': 'school15.dushanbe@smartlib.tj',
                'student_capacity': 1200,
                'is_active': True,
            }
        )

        school20, _ = School.objects.get_or_create(
            school_number='20',
            defaults={
                'name': 'Гимназияи №20 ба номи А. Фирдавсӣ',
                'region': reg_dushanbe,
                'district': dist_sino,
                'jamoat': jam_sino1,
                'address': 'ш. Душанбе, кӯчаи Сино 45',
                'phone': '+992 37 233-20-20',
                'email': 'gymnasium20@smartlib.tj',
                'student_capacity': 900,
                'is_active': True,
            }
        )

        # 4. Users for all 7 roles
        # Super Admin
        super_admin, _ = User.objects.get_or_create(
            username='admin',
            defaults={
                'first_name': 'Фирдавс',
                'last_name': 'Каримов',
                'email': 'admin@smartlib.tj',
                'role': User.Role.SUPER_ADMIN,
                'is_staff': True,
                'is_superuser': True,
                'is_active': True,
            }
        )
        super_admin.set_password('admin123')
        super_admin.save()

        # District Chairman
        district_chairman, _ = User.objects.get_or_create(
            username='district_somoni',
            defaults={
                'first_name': 'Рустам',
                'last_name': 'Аҳмадов',
                'email': 'somoni.edu@smartlib.tj',
                'role': User.Role.DISTRICT_CHAIRMAN,
                'region': reg_dushanbe,
                'district': dist_somoni,
                'is_active': True,
            }
        )
        district_chairman.set_password('admin123')
        district_chairman.save()

        # Jamoat Chairman
        jamoat_chairman, _ = User.objects.get_or_create(
            username='jamoat_leader',
            defaults={
                'first_name': 'Сӯҳроб',
                'last_name': 'Назаров',
                'email': 'jamoat.leader@smartlib.tj',
                'role': User.Role.JAMOAT_CHAIRMAN,
                'region': reg_dushanbe,
                'district': dist_somoni,
                'jamoat': jam_somoni1,
                'is_active': True,
            }
        )
        jamoat_chairman.set_password('admin123')
        jamoat_chairman.save()

        # School Director
        director, _ = User.objects.get_or_create(
            username='director_15',
            defaults={
                'first_name': 'Дилшод',
                'last_name': 'Саидов',
                'email': 'director15@smartlib.tj',
                'role': User.Role.SCHOOL_DIRECTOR,
                'school': school15,
                'region': reg_dushanbe,
                'district': dist_somoni,
                'jamoat': jam_somoni1,
                'is_active': True,
            }
        )
        director.set_password('admin123')
        director.save()

        # Librarian
        librarian, _ = User.objects.get_or_create(
            username='librarian_15',
            defaults={
                'first_name': 'Нигора',
                'last_name': 'Юсупова',
                'email': 'librarian15@smartlib.tj',
                'role': User.Role.LIBRARIAN,
                'school': school15,
                'region': reg_dushanbe,
                'district': dist_somoni,
                'jamoat': jam_somoni1,
                'is_active': True,
            }
        )
        librarian.set_password('admin123')
        librarian.save()

        # Class Teacher
        teacher, _ = User.objects.get_or_create(
            username='teacher_rustam',
            defaults={
                'first_name': 'Муҳаммад',
                'last_name': 'Раҳимов',
                'email': 'teacher.rahimov@smartlib.tj',
                'role': User.Role.CLASS_TEACHER,
                'school': school15,
                'region': reg_dushanbe,
                'district': dist_somoni,
                'jamoat': jam_somoni1,
                'is_active': True,
            }
        )
        teacher.set_password('admin123')
        teacher.save()

        # Students
        student1, _ = User.objects.get_or_create(
            username='student_anisa',
            defaults={
                'first_name': 'Аниса',
                'last_name': 'Шарипова',
                'email': 'anisa.sh@smartlib.tj',
                'role': User.Role.STUDENT,
                'school': school15,
                'region': reg_dushanbe,
                'district': dist_somoni,
                'jamoat': jam_somoni1,
                'is_active': True,
            }
        )
        student1.set_password('admin123')
        student1.save()

        student2, _ = User.objects.get_or_create(
            username='student_davron',
            defaults={
                'first_name': 'Даврон',
                'last_name': 'Холиқов',
                'email': 'davron.kh@smartlib.tj',
                'role': User.Role.STUDENT,
                'school': school15,
                'region': reg_dushanbe,
                'district': dist_somoni,
                'jamoat': jam_somoni1,
                'is_active': True,
            }
        )
        student2.set_password('admin123')
        student2.save()

        # 5. Classrooms & Assignments
        class_10a, _ = Classroom.objects.get_or_create(
            school=school15,
            name='10-А',
            academic_year=year,
            defaults={'grade': 10}
        )
        class_10b, _ = Classroom.objects.get_or_create(
            school=school15,
            name='10-Б',
            academic_year=year,
            defaults={'grade': 10}
        )
        class_9a, _ = Classroom.objects.get_or_create(
            school=school15,
            name='9-А',
            academic_year=year,
            defaults={'grade': 9}
        )

        # Teacher Assignment
        TeacherClassAssignment.objects.get_or_create(
            teacher=teacher,
            classroom=class_10a,
            academic_year=year,
            defaults={'is_class_teacher': True}
        )

        # Student Enrollments
        StudentEnrollment.objects.get_or_create(
            student=student1,
            academic_year=year,
            defaults={'classroom': class_10a, 'is_active': True}
        )
        StudentEnrollment.objects.get_or_create(
            student=student2,
            academic_year=year,
            defaults={'classroom': class_10a, 'is_active': True}
        )

        # 6. Book Catalog
        books_data = [
            {'title': 'Алгебра ва ибтидои таҳлил (10 синф)', 'author': 'Ш. Алимов, Ю. Колягин', 'subject': 'Алгебра', 'grade': 10, 'lang': 'tj', 'isbn': '978-99947-1-101-1'},
            {'title': 'Забони тоҷикӣ (10 синф)', 'author': 'С. Ҳошимов, Д. Шарипова', 'subject': 'Забони тоҷикӣ', 'grade': 10, 'lang': 'tj', 'isbn': '978-99947-1-102-8'},
            {'title': 'Таърихи халқи тоҷик (10 синф)', 'author': 'Н. Ҳотамов, Р. Набиева', 'subject': 'Таърих', 'grade': 10, 'lang': 'tj', 'isbn': '978-99947-1-103-5'},
            {'title': 'Физика (10 синф)', 'author': 'Г. Мякишев, Б. Буховцев', 'subject': 'Физика', 'grade': 10, 'lang': 'tj', 'isbn': '978-99947-1-104-2'},
            {'title': 'Химия (10 синф)', 'author': 'О. Габриелян', 'subject': 'Химия', 'grade': 10, 'lang': 'tj', 'isbn': '978-99947-1-105-9'},
            {'title': 'Геометрия (10 синф)', 'author': 'Л. Атанасян', 'subject': 'Геометрия', 'grade': 10, 'lang': 'ru', 'isbn': '978-99947-1-106-6'},
        ]

        # Extra textbooks covering grades 1-9 and 11, so the catalog spans the whole school (1-11 синф)
        extra_books_by_grade = {
            1: [
                ('Алифбо (синфи 1)', 'М. Лутфуллозода, С. Сулаймонӣ', 'Алифбо', 'tj'),
                ('Математика (синфи 1)', 'Р. Исмоилова, Ф. Раҷабова', 'Математика', 'tj'),
                ('Забони модарӣ (синфи 1)', 'Д. Худойдодова', 'Забони тоҷикӣ', 'tj'),
                ('Одобнома (синфи 1)', 'Н. Сайфуллоева', 'Одобнома', 'tj'),
            ],
            2: [
                ('Забони тоҷикӣ (синфи 2)', 'М. Лутфуллозода', 'Забони тоҷикӣ', 'tj'),
                ('Математика (синфи 2)', 'Р. Исмоилова', 'Математика', 'tj'),
                ('Забони русӣ (синфи 2)', 'Т. Розенталь, Н. Пахомова', 'Забони русӣ', 'ru'),
                ('Дунёи атроф (синфи 2)', 'Ш. Раҳимова', 'Дунёи атроф', 'tj'),
            ],
            3: [
                ('Забони тоҷикӣ (синфи 3)', 'М. Лутфуллозода', 'Забони тоҷикӣ', 'tj'),
                ('Математика (синфи 3)', 'Р. Исмоилова', 'Математика', 'tj'),
                ('Забони русӣ (синфи 3)', 'Т. Розенталь', 'Забони русӣ', 'ru'),
                ('Табиатшиносӣ (синфи 3)', 'Ф. Қодирова', 'Табиатшиносӣ', 'tj'),
                ('Санъат (синфи 3)', 'Г. Назарова', 'Санъат', 'tj'),
            ],
            4: [
                ('Забони тоҷикӣ (синфи 4)', 'М. Лутфуллозода', 'Забони тоҷикӣ', 'tj'),
                ('Математика (синфи 4)', 'Р. Исмоилова', 'Математика', 'tj'),
                ('Забони русӣ (синфи 4)', 'Т. Розенталь', 'Забони русӣ', 'ru'),
                ('Забони англисӣ (синфи 4)', 'М. Азимова, Ҷ. Смит', 'Забони англисӣ', 'tj'),
                ('Табиатшиносӣ (синфи 4)', 'Ф. Қодирова', 'Табиатшиносӣ', 'tj'),
            ],
            5: [
                ('Забони тоҷикӣ (синфи 5)', 'С. Ҳошимов', 'Забони тоҷикӣ', 'tj'),
                ('Адабиёти тоҷик (синфи 5)', 'Х. Шарифов', 'Адабиёт', 'tj'),
                ('Математика (синфи 5)', 'Н. Виленкин', 'Математика', 'tj'),
                ('Забони русӣ (синфи 5)', 'Т. Розенталь', 'Забони русӣ', 'ru'),
                ('Забони англисӣ (синфи 5)', 'М. Азимова', 'Забони англисӣ', 'tj'),
                ('Таърихи қадим (синфи 5)', 'А. Мухторов', 'Таърих', 'tj'),
            ],
            6: [
                ('Забони тоҷикӣ (синфи 6)', 'С. Ҳошимов', 'Забони тоҷикӣ', 'tj'),
                ('Адабиёти тоҷик (синфи 6)', 'Х. Шарифов', 'Адабиёт', 'tj'),
                ('Математика (синфи 6)', 'Н. Виленкин', 'Математика', 'tj'),
                ('Забони русӣ (синфи 6)', 'Т. Розенталь', 'Забони русӣ', 'ru'),
                ('Забони англисӣ (синфи 6)', 'М. Азимова', 'Забони англисӣ', 'tj'),
                ('Ҷуғрофияи қитъаҳо (синфи 6)', 'Қ. Абдулназаров', 'Ҷуғрофия', 'tj'),
                ('Биология (синфи 6)', 'В. Пасечник', 'Биология', 'tj'),
            ],
            7: [
                ('Алгебра (синфи 7)', 'Ш. Алимов', 'Алгебра', 'tj'),
                ('Геометрия (синфи 7)', 'Л. Атанасян', 'Геометрия', 'ru'),
                ('Забони тоҷикӣ (синфи 7)', 'С. Ҳошимов', 'Забони тоҷикӣ', 'tj'),
                ('Адабиёти тоҷик (синфи 7)', 'Х. Шарифов', 'Адабиёт', 'tj'),
                ('Забони русӣ (синфи 7)', 'Т. Розенталь', 'Забони русӣ', 'ru'),
                ('Забони англисӣ (синфи 7)', 'М. Азимова', 'Забони англисӣ', 'tj'),
                ('Физика (синфи 7)', 'А. Пёрышкин', 'Физика', 'tj'),
                ('Ҷуғрофияи Тоҷикистон (синфи 7)', 'Қ. Абдулназаров', 'Ҷуғрофия', 'tj'),
            ],
            8: [
                ('Алгебра (синфи 8)', 'Ш. Алимов', 'Алгебра', 'tj'),
                ('Геометрия (синфи 8)', 'Л. Атанасян', 'Геометрия', 'ru'),
                ('Физика (синфи 8)', 'А. Пёрышкин', 'Физика', 'tj'),
                ('Химия (синфи 8)', 'О. Габриелян', 'Химия', 'tj'),
                ('Биология (синфи 8)', 'В. Пасечник', 'Биология', 'tj'),
                ('Таърихи умумиҷаҳонӣ (синфи 8)', 'А. Мухторов', 'Таърих', 'tj'),
                ('Забони тоҷикӣ (синфи 8)', 'С. Ҳошимов', 'Забони тоҷикӣ', 'tj'),
                ('Забони англисӣ (синфи 8)', 'М. Азимова', 'Забони англисӣ', 'tj'),
            ],
            9: [
                ('Алгебра (синфи 9)', 'Ш. Алимов', 'Алгебра', 'tj'),
                ('Геометрия (синфи 9)', 'Л. Атанасян', 'Геометрия', 'ru'),
                ('Физика (синфи 9)', 'А. Пёрышкин', 'Физика', 'tj'),
                ('Химия (синфи 9)', 'О. Габриелян', 'Химия', 'tj'),
                ('Биология (синфи 9)', 'В. Пасечник', 'Биология', 'tj'),
                ('Ҷуғрофияи ҷаҳон (синфи 9)', 'Қ. Абдулназаров', 'Ҷуғрофия', 'tj'),
                ('Таърихи халқи тоҷик (синфи 9)', 'Н. Ҳотамов', 'Таърих', 'tj'),
                ('Информатика (синфи 9)', 'Л. Босова', 'Информатика', 'tj'),
                ('Забони англисӣ (синфи 9)', 'М. Азимова', 'Забони англисӣ', 'tj'),
            ],
            10: [
                ('Биология (синфи 10)', 'В. Пасечник', 'Биология', 'tj'),
                ('Забони англисӣ (синфи 10)', 'М. Азимова', 'Забони англисӣ', 'tj'),
                ('Информатика (синфи 10)', 'Л. Босова', 'Информатика', 'tj'),
            ],
            11: [
                ('Алгебра ва ибтидои таҳлил (синфи 11)', 'Ш. Алимов', 'Алгебра', 'tj'),
                ('Геометрия (синфи 11)', 'Л. Атанасян', 'Геометрия', 'ru'),
                ('Физика (синфи 11)', 'Г. Мякишев', 'Физика', 'tj'),
                ('Химия (синфи 11)', 'О. Габриелян', 'Химия', 'tj'),
                ('Биология (синфи 11)', 'В. Пасечник', 'Биология', 'tj'),
                ('Забони тоҷикӣ (синфи 11)', 'С. Ҳошимов', 'Забони тоҷикӣ', 'tj'),
                ('Адабиёти тоҷик (синфи 11)', 'Х. Шарифов', 'Адабиёт', 'tj'),
                ('Таърихи умумиҷаҳонӣ (синфи 11)', 'А. Мухторов', 'Таърих', 'tj'),
                ('Асосҳои амнияти ҳаёт (синфи 11)', 'Ф. Раҳмонов', 'ОБҲ', 'tj'),
            ],
        }

        isbn_seq = 107
        for grade, items in extra_books_by_grade.items():
            for title, author, subject, lang in items:
                books_data.append({
                    'title': title,
                    'author': author,
                    'subject': subject,
                    'grade': grade,
                    'lang': lang,
                    'isbn': f'978-99947-1-{isbn_seq:03d}-1',
                })
                isbn_seq += 1

        created_books = []
        for bd in books_data:
            book, _ = Book.objects.get_or_create(
                isbn=bd['isbn'],
                defaults={
                    'title': bd['title'],
                    'author': bd['author'],
                    'subject': bd['subject'],
                    'grade': bd['grade'],
                    'language': bd['lang'],
                    'publisher': 'Маориф ва фарҳанг',
                    'publication_year': 2024,
                }
            )
            created_books.append(book)

        # 7. Book Copies & Full Movement Chain for School №15
        for idx, book in enumerate(created_books):
            for copy_i in range(1, 11):
                inv = f'TJ-S015-B{book.pk:04d}-{copy_i:05d}'
                bc = f'BC015{book.pk:04d}{copy_i:05d}'
                copy, created = BookCopy.objects.get_or_create(
                    inventory_number=inv,
                    defaults={
                        'book': book,
                        'barcode': bc,
                        'school': school15,
                        'status': BookCopy.Status.AT_LIBRARY,
                    }
                )

                if created:
                    # Warehouse to School
                    BookTransaction.objects.create(
                        book_copy=copy,
                        from_user=None,
                        to_user=librarian,
                        from_location='Маркази тақсимоти Вазорати маориф',
                        to_location=f'Китобхонаи МТМУ №15',
                        transaction_type=BookTransaction.TransactionType.WAREHOUSE_TO_SCHOOL,
                        created_by=super_admin,
                        note='Оприходование тиража 2024 года'
                    )

                    # Exemplify full custody chain:
                    # Copy 1 goes: Librarian -> Teacher -> Student1
                    if copy_i == 1 and idx < 3:
                        copy.status = BookCopy.Status.ISSUED_TO_STUDENT
                        copy.save()

                        # Librarian -> Teacher
                        BookTransaction.objects.create(
                            book_copy=copy,
                            from_user=librarian,
                            to_user=teacher,
                            from_location=f'Китобхонаи МТМУ №15',
                            to_location=f'Роҳбари синф {teacher.get_full_name()}',
                            transaction_type=BookTransaction.TransactionType.LIBRARIAN_TO_TEACHER,
                            created_by=librarian,
                            note='Супоридан ба роҳбари синфи 10-А'
                        )
                        # Teacher -> Student
                        BookTransaction.objects.create(
                            book_copy=copy,
                            from_user=teacher,
                            to_user=student1,
                            from_location=f'Роҳбари синф {teacher.get_full_name()}',
                            to_location=f'Хонанда {student1.get_full_name()} (10-А)',
                            transaction_type=BookTransaction.TransactionType.TEACHER_TO_STUDENT,
                            created_by=teacher,
                            note='Супоридан ба хонанда барои соли хониш'
                        )

                    # Copy 2 goes: Librarian -> Teacher (ready with teacher)
                    elif copy_i == 2 and idx < 3:
                        copy.status = BookCopy.Status.ISSUED_TO_TEACHER
                        copy.save()

                        BookTransaction.objects.create(
                            book_copy=copy,
                            from_user=librarian,
                            to_user=teacher,
                            from_location=f'Китобхонаи МТМУ №15',
                            to_location=f'Роҳбари синф {teacher.get_full_name()}',
                            transaction_type=BookTransaction.TransactionType.LIBRARIAN_TO_TEACHER,
                            created_by=librarian,
                            note='Барои тақсимот ба хонандагон'
                        )

        # 8. Demo Book Request & Issue
        if created_books:
            BookRequest.objects.get_or_create(
                school=school15,
                book=created_books[0],
                defaults={
                    'requested_quantity': 45,
                    'available_quantity': 10,
                    'reason': 'Зиёд шудани шумораи хонандагони синфи 10 дар соли хониши нав',
                    'status': BookRequest.Status.PENDING,
                    'created_by': director,
                }
            )

        log_audit(super_admin, 'DATABASE_SEED', 'System', '', 'Full database seeding executed successfully.')
        self.stdout.write(self.style.SUCCESS('\n========================================='))
        self.stdout.write(self.style.SUCCESS('Smart Library TJ demo data successfully initialized!'))
        self.stdout.write(self.style.SUCCESS('Available accounts (Password for all: admin123):'))
        self.stdout.write(self.style.SUCCESS('1. Super Admin:       admin'))
        self.stdout.write(self.style.SUCCESS('2. District Chairman: district_somoni'))
        self.stdout.write(self.style.SUCCESS('3. Jamoat Chairman:   jamoat_leader'))
        self.stdout.write(self.style.SUCCESS('4. School Director:   director_15'))
        self.stdout.write(self.style.SUCCESS('5. Librarian:         librarian_15'))
        self.stdout.write(self.style.SUCCESS('6. Class Teacher:     teacher_rustam'))
        self.stdout.write(self.style.SUCCESS('7. Student:           student_anisa / student_davron'))
        self.stdout.write(self.style.SUCCESS('=========================================\n'))
