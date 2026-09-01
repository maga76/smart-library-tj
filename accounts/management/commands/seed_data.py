import datetime
import random
from django.core.management.base import BaseCommand
from accounts.models import User
from geography.models import Region, District, Jamoat
from schools.models import School
from library.models import (
    AcademicYear, Classroom, StudentEnrollment, TeacherClassAssignment,
    Book, BookCopy, BookRequest
)
from transactions.models import BookTransaction
from audit.utils import log_audit

# Fixed seed so re-running the command always generates the same demo names.
random.seed(20260901)

MALE_FIRST_NAMES = [
    'Алишер', 'Фаридун', 'Шерали', 'Хуршед', 'Далер', 'Умарали', 'Ҷасур', 'Некрӯз',
    'Парвиз', 'Бахтиёр', 'Файзали', 'Саидҷон', 'Абдуҷаббор', 'Исмоил', 'Раҳматулло',
    'Наимҷон', 'Шамсиддин', 'Нуриддин', 'Хусрав', 'Собир', 'Ориф', 'Кароматулло',
    'Зафар', 'Иброҳим',
]
FEMALE_FIRST_NAMES = [
    'Гулнора', 'Мунира', 'Шаҳноза', 'Дилрабо', 'Нигина', 'Мадина', 'Замира', 'Сабоҳат',
    'Фарзона', 'Ойгул', 'Рухшона', 'Сабрина', 'Зулфия', 'Гулбаҳор', 'Малоҳат', 'Насиба',
    'Тахмина', 'Шоира', 'Дилноза', 'Меҳрубон', 'Нозанин', 'Саодат', 'Фирӯза', 'Ҳилола',
]
SURNAME_STEMS = [
    'Раҷаб', 'Карим', 'Назар', 'Юсуф', 'Саид', 'Ҳайдар', 'Раҳим', 'Сафар', 'Эргаш',
    'Холиқ', 'Мирзо', 'Вали', 'Абдулло', 'Исмоил', 'Шариф', 'Файзулло', 'Комил',
    'Ҳаким', 'Бобо', 'Ғаффор', 'Латиф', 'Наврӯз', 'Пирмуҳаммад', 'Қурбон',
]


def _random_person(gender):
    """Return (first_name, last_name) for a demo user of the given gender ('M'/'F')."""
    stem = random.choice(SURNAME_STEMS)
    if gender == 'M':
        return random.choice(MALE_FIRST_NAMES), stem + 'ов'
    return random.choice(FEMALE_FIRST_NAMES), stem + 'ова'


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
        dist_isfara, _ = District.objects.get_or_create(
            code='ISFARA',
            defaults={'region': reg_sughd, 'name_tj': 'Шаҳри Исфара', 'name_ru': 'город Исфара', 'is_active': True}
        )
        dist_firdavsi, _ = District.objects.get_or_create(
            code='FIRDAVSI',
            defaults={'region': reg_dushanbe, 'name_tj': 'Ноҳияи Фирдавсӣ', 'name_ru': 'Район Фирдавси', 'is_active': True}
        )
        dist_bokhtar, _ = District.objects.get_or_create(
            code='BOKHTAR',
            defaults={'region': reg_khatlon, 'name_tj': 'Шаҳри Бохтар', 'name_ru': 'город Бохтар', 'is_active': True}
        )
        dist_kulob, _ = District.objects.get_or_create(
            code='KULOB',
            defaults={'region': reg_khatlon, 'name_tj': 'Шаҳри Кӯлоб', 'name_ru': 'город Куляб', 'is_active': True}
        )
        dist_khorugh, _ = District.objects.get_or_create(
            code='KHORUGH',
            defaults={'region': reg_gbao, 'name_tj': 'Шаҳри Хоруғ', 'name_ru': 'город Хорог', 'is_active': True}
        )
        dist_vahdat, _ = District.objects.get_or_create(
            code='VAHDAT',
            defaults={'region': reg_rrs, 'name_tj': 'Шаҳри Ваҳдат', 'name_ru': 'город Вахдат', 'is_active': True}
        )
        dist_hisor, _ = District.objects.get_or_create(
            code='HISOR',
            defaults={'region': reg_rrs, 'name_tj': 'Ноҳияи Ҳисор', 'name_ru': 'Гиссарский район', 'is_active': True}
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
        jam_khujand1, _ = Jamoat.objects.get_or_create(
            district=dist_khujand,
            name_ru='Маҳаллаи Марказӣ (Хуҷанд)',
            defaults={'name_tj': 'Маҳаллаи Марказӣ (Хуҷанд)', 'is_active': True}
        )
        jam_isfara1, _ = Jamoat.objects.get_or_create(
            district=dist_isfara, name_ru='Маҳаллаи Марказӣ (Исфара)',
            defaults={'name_tj': 'Маҳаллаи Марказӣ (Исфара)', 'is_active': True}
        )
        jam_firdavsi1, _ = Jamoat.objects.get_or_create(
            district=dist_firdavsi, name_ru='Маҳаллаи Фирдавсӣ-1',
            defaults={'name_tj': 'Маҳаллаи Фирдавсӣ-1', 'is_active': True}
        )
        jam_bokhtar1, _ = Jamoat.objects.get_or_create(
            district=dist_bokhtar, name_ru='Маҳаллаи Марказӣ (Бохтар)',
            defaults={'name_tj': 'Маҳаллаи Марказӣ (Бохтар)', 'is_active': True}
        )
        jam_kulob1, _ = Jamoat.objects.get_or_create(
            district=dist_kulob, name_ru='Маҳаллаи Марказӣ (Кӯлоб)',
            defaults={'name_tj': 'Маҳаллаи Марказӣ (Кӯлоб)', 'is_active': True}
        )
        jam_khorugh1, _ = Jamoat.objects.get_or_create(
            district=dist_khorugh, name_ru='Маҳаллаи Марказӣ (Хоруғ)',
            defaults={'name_tj': 'Маҳаллаи Марказӣ (Хоруғ)', 'is_active': True}
        )
        jam_vahdat1, _ = Jamoat.objects.get_or_create(
            district=dist_vahdat, name_ru='Маҳаллаи Марказӣ (Ваҳдат)',
            defaults={'name_tj': 'Маҳаллаи Марказӣ (Ваҳдат)', 'is_active': True}
        )
        jam_hisor1, _ = Jamoat.objects.get_or_create(
            district=dist_hisor, name_ru='Ҷамоати деҳоти Ҳисор',
            defaults={'name_tj': 'Ҷамоати деҳоти Ҳисор', 'is_active': True}
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

        school5, _ = School.objects.get_or_create(
            school_number='5',
            defaults={
                'name': 'Мактаби таҳсилоти миёнаи умумии №5',
                'region': reg_sughd,
                'district': dist_khujand,
                'jamoat': jam_khujand1,
                'address': 'ш. Хуҷанд, кӯчаи Ленин 30',
                'phone': '+992 34 222-05-05',
                'email': 'school5.khujand@smartlib.tj',
                'student_capacity': 800,
                'is_active': True,
            }
        )

        # 3b. Additional schools spread across every region, so district/jamoat
        # chairman dashboards and the national analytics have real coverage.
        new_schools_specs = [
            {'number': '1', 'name': 'Мактаби таҳсилоти миёнаи умумии №1', 'region': reg_khatlon, 'district': dist_bokhtar, 'jamoat': jam_bokhtar1, 'city': 'ш. Бохтар', 'cap': 700},
            {'number': '2', 'name': 'Мактаби таҳсилоти миёнаи умумии №2', 'region': reg_khatlon, 'district': dist_bokhtar, 'jamoat': jam_bokhtar1, 'city': 'ш. Бохтар', 'cap': 650},
            {'number': '3', 'name': 'Мактаби таҳсилоти миёнаи умумии №3', 'region': reg_khatlon, 'district': dist_kulob, 'jamoat': jam_kulob1, 'city': 'ш. Кӯлоб', 'cap': 750},
            {'number': '4', 'name': 'Гимназияи №4 ба номи Абӯалӣ ибни Сино', 'region': reg_gbao, 'district': dist_khorugh, 'jamoat': jam_khorugh1, 'city': 'ш. Хоруғ', 'cap': 500},
            {'number': '8', 'name': 'Мактаби таҳсилоти миёнаи умумии №8', 'region': reg_rrs, 'district': dist_vahdat, 'jamoat': jam_vahdat1, 'city': 'ш. Ваҳдат', 'cap': 680},
            {'number': '9', 'name': 'Мактаби таҳсилоти миёнаи умумии №9', 'region': reg_rrs, 'district': dist_hisor, 'jamoat': jam_hisor1, 'city': 'н. Ҳисор', 'cap': 620},
            {'number': '12', 'name': 'Мактаби таҳсилоти миёнаи умумии №12', 'region': reg_sughd, 'district': dist_isfara, 'jamoat': jam_isfara1, 'city': 'ш. Исфара', 'cap': 700},
            {'number': '13', 'name': 'Литсейи ихтисоси №13', 'region': reg_sughd, 'district': dist_isfara, 'jamoat': jam_isfara1, 'city': 'ш. Исфара', 'cap': 450},
            {'number': '17', 'name': 'Мактаби таҳсилоти миёнаи умумии №17', 'region': reg_dushanbe, 'district': dist_firdavsi, 'jamoat': jam_firdavsi1, 'city': 'ш. Душанбе', 'cap': 900},
            {'number': '21', 'name': 'Мактаби таҳсилоти миёнаи умумии №21', 'region': reg_dushanbe, 'district': dist_sino, 'jamoat': jam_sino1, 'city': 'ш. Душанбе', 'cap': 850},
            {'number': '34', 'name': 'Мактаби таҳсилоти миёнаи умумии №34', 'region': reg_sughd, 'district': dist_khujand, 'jamoat': jam_khujand1, 'city': 'ш. Хуҷанд', 'cap': 780},
            {'number': '40', 'name': 'Гимназияи №40 ба номи Рӯдакӣ', 'region': reg_dushanbe, 'district': dist_somoni, 'jamoat': jam_somoni1, 'city': 'ш. Душанбе', 'cap': 950},
        ]
        new_schools = []
        for spec in new_schools_specs:
            school_obj, _ = School.objects.get_or_create(
                school_number=spec['number'],
                defaults={
                    'name': spec['name'],
                    'region': spec['region'],
                    'district': spec['district'],
                    'jamoat': spec['jamoat'],
                    'address': f"{spec['city']}, мактаби №{spec['number']}",
                    'phone': f"+992 37 {int(spec['number']):03d}-00-00",
                    'email': f"school{spec['number']}@smartlib.tj",
                    'student_capacity': spec['cap'],
                    'is_active': True,
                }
            )
            new_schools.append(school_obj)
        self.stdout.write(self.style.SUCCESS(f'Additional schools: {len(new_schools)}'))

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

        # 4b. Users for School №20 and School №5
        director_20, _ = User.objects.get_or_create(
            username='director_20',
            defaults={
                'first_name': 'Ҷамшед', 'last_name': 'Раҷабов', 'email': 'director20@smartlib.tj',
                'role': User.Role.SCHOOL_DIRECTOR, 'school': school20,
                'region': reg_dushanbe, 'district': dist_sino, 'jamoat': jam_sino1, 'is_active': True,
            }
        )
        director_20.set_password('admin123')
        director_20.save()

        librarian_20, _ = User.objects.get_or_create(
            username='librarian_20',
            defaults={
                'first_name': 'Мадина', 'last_name': 'Қосимова', 'email': 'librarian20@smartlib.tj',
                'role': User.Role.LIBRARIAN, 'school': school20,
                'region': reg_dushanbe, 'district': dist_sino, 'jamoat': jam_sino1, 'is_active': True,
            }
        )
        librarian_20.set_password('admin123')
        librarian_20.save()

        teacher_20, _ = User.objects.get_or_create(
            username='teacher_muzaffar',
            defaults={
                'first_name': 'Музаффар', 'last_name': 'Ҷӯраев', 'email': 'teacher.juraev@smartlib.tj',
                'role': User.Role.CLASS_TEACHER, 'school': school20,
                'region': reg_dushanbe, 'district': dist_sino, 'jamoat': jam_sino1, 'is_active': True,
            }
        )
        teacher_20.set_password('admin123')
        teacher_20.save()

        student_karim, _ = User.objects.get_or_create(
            username='student_karim',
            defaults={
                'first_name': 'Карим', 'last_name': 'Раҳмонов', 'email': 'karim.r@smartlib.tj',
                'role': User.Role.STUDENT, 'school': school20,
                'region': reg_dushanbe, 'district': dist_sino, 'jamoat': jam_sino1, 'is_active': True,
            }
        )
        student_karim.set_password('admin123')
        student_karim.save()

        student_malika, _ = User.objects.get_or_create(
            username='student_malika',
            defaults={
                'first_name': 'Малика', 'last_name': 'Эргашева', 'email': 'malika.e@smartlib.tj',
                'role': User.Role.STUDENT, 'school': school20,
                'region': reg_dushanbe, 'district': dist_sino, 'jamoat': jam_sino1, 'is_active': True,
            }
        )
        student_malika.set_password('admin123')
        student_malika.save()

        director_5, _ = User.objects.get_or_create(
            username='director_5',
            defaults={
                'first_name': 'Фарҳод', 'last_name': 'Иброҳимов', 'email': 'director5@smartlib.tj',
                'role': User.Role.SCHOOL_DIRECTOR, 'school': school5,
                'region': reg_sughd, 'district': dist_khujand, 'jamoat': jam_khujand1, 'is_active': True,
            }
        )
        director_5.set_password('admin123')
        director_5.save()

        librarian_5, _ = User.objects.get_or_create(
            username='librarian_5',
            defaults={
                'first_name': 'Зарина', 'last_name': 'Сафарова', 'email': 'librarian5@smartlib.tj',
                'role': User.Role.LIBRARIAN, 'school': school5,
                'region': reg_sughd, 'district': dist_khujand, 'jamoat': jam_khujand1, 'is_active': True,
            }
        )
        librarian_5.set_password('admin123')
        librarian_5.save()

        teacher_5, _ = User.objects.get_or_create(
            username='teacher_5',
            defaults={
                'first_name': 'Абдулло', 'last_name': 'Назаров', 'email': 'teacher.nazarov@smartlib.tj',
                'role': User.Role.CLASS_TEACHER, 'school': school5,
                'region': reg_sughd, 'district': dist_khujand, 'jamoat': jam_khujand1, 'is_active': True,
            }
        )
        teacher_5.set_password('admin123')
        teacher_5.save()

        student_5a, _ = User.objects.get_or_create(
            username='student_5a',
            defaults={
                'first_name': 'Фирӯза', 'last_name': 'Мирзоева', 'email': 'firuza.m@smartlib.tj',
                'role': User.Role.STUDENT, 'school': school5,
                'region': reg_sughd, 'district': dist_khujand, 'jamoat': jam_khujand1, 'is_active': True,
            }
        )
        student_5a.set_password('admin123')
        student_5a.save()

        student_5b, _ = User.objects.get_or_create(
            username='student_5b',
            defaults={
                'first_name': 'Умед', 'last_name': 'Валиев', 'email': 'umed.v@smartlib.tj',
                'role': User.Role.STUDENT, 'school': school5,
                'region': reg_sughd, 'district': dist_khujand, 'jamoat': jam_khujand1, 'is_active': True,
            }
        )
        student_5b.set_password('admin123')
        student_5b.save()

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

        # Classrooms & enrollments for School №20 and School №5
        class_20_10a, _ = Classroom.objects.get_or_create(
            school=school20, name='10-А', academic_year=year, defaults={'grade': 10}
        )
        class_5_10a, _ = Classroom.objects.get_or_create(
            school=school5, name='10-А', academic_year=year, defaults={'grade': 10}
        )

        TeacherClassAssignment.objects.get_or_create(
            teacher=teacher_20, classroom=class_20_10a, academic_year=year,
            defaults={'is_class_teacher': True}
        )
        TeacherClassAssignment.objects.get_or_create(
            teacher=teacher_5, classroom=class_5_10a, academic_year=year,
            defaults={'is_class_teacher': True}
        )

        StudentEnrollment.objects.get_or_create(
            student=student_karim, academic_year=year,
            defaults={'classroom': class_20_10a, 'is_active': True}
        )
        StudentEnrollment.objects.get_or_create(
            student=student_malika, academic_year=year,
            defaults={'classroom': class_20_10a, 'is_active': True}
        )
        StudentEnrollment.objects.get_or_create(
            student=student_5a, academic_year=year,
            defaults={'classroom': class_5_10a, 'is_active': True}
        )
        StudentEnrollment.objects.get_or_create(
            student=student_5b, academic_year=year,
            defaults={'classroom': class_5_10a, 'is_active': True}
        )

        # 5b. Staff & students for the additional schools — generated from name
        # pools so every region gets a realistic amount of teachers, librarians
        # and students without hand-typing each one.
        GRADES_PER_SCHOOL = [1, 3, 5, 7, 9, 11]
        STUDENTS_PER_CLASS = 15
        new_school_users = 0
        school_librarians = {}

        for school_obj in new_schools:
            num = school_obj.school_number
            common = {
                'region': school_obj.region, 'district': school_obj.district,
                'jamoat': school_obj.jamoat, 'school': school_obj, 'is_active': True,
            }

            d_first, d_last = _random_person(random.choice('MF'))
            director_obj, created = User.objects.get_or_create(
                username=f'director_s{num}',
                defaults={**common, 'first_name': d_first, 'last_name': d_last,
                          'email': f'director.s{num}@smartlib.tj', 'role': User.Role.SCHOOL_DIRECTOR}
            )
            if created:
                director_obj.set_password('admin123')
                director_obj.save()
                new_school_users += 1

            librarian_count = 2 if school_obj.student_capacity >= 800 else 1
            for i in range(1, librarian_count + 1):
                first, last = _random_person(random.choice('FFM'))
                lib, created = User.objects.get_or_create(
                    username=f'librarian_s{num}_{i}',
                    defaults={**common, 'first_name': first, 'last_name': last,
                              'email': f'librarian.s{num}.{i}@smartlib.tj', 'role': User.Role.LIBRARIAN}
                )
                if created:
                    lib.set_password('admin123')
                    lib.save()
                    new_school_users += 1
                if i == 1:
                    school_librarians[school_obj.pk] = lib

            for ci, grade in enumerate(GRADES_PER_SCHOOL, start=1):
                classroom, _ = Classroom.objects.get_or_create(
                    school=school_obj, name=f'{grade}-А', academic_year=year,
                    defaults={'grade': grade}
                )

                t_first, t_last = _random_person(random.choice('MF'))
                teacher_obj, created = User.objects.get_or_create(
                    username=f'teacher_s{num}_{ci}',
                    defaults={**common, 'first_name': t_first, 'last_name': t_last,
                              'email': f'teacher.s{num}.{ci}@smartlib.tj', 'role': User.Role.CLASS_TEACHER}
                )
                if created:
                    teacher_obj.set_password('admin123')
                    teacher_obj.save()
                    new_school_users += 1

                TeacherClassAssignment.objects.get_or_create(
                    teacher=teacher_obj, classroom=classroom, academic_year=year,
                    defaults={'is_class_teacher': True}
                )

                for si in range(1, STUDENTS_PER_CLASS + 1):
                    s_first, s_last = _random_person(random.choice('MF'))
                    student_obj, created = User.objects.get_or_create(
                        username=f'student_s{num}_{ci}_{si}',
                        defaults={**common, 'first_name': s_first, 'last_name': s_last,
                                  'email': f'student.s{num}.{ci}.{si}@smartlib.tj', 'role': User.Role.STUDENT}
                    )
                    if created:
                        student_obj.set_password('admin123')
                        student_obj.save()
                        new_school_users += 1

                    StudentEnrollment.objects.get_or_create(
                        student=student_obj, academic_year=year,
                        defaults={'classroom': classroom, 'is_active': True}
                    )

        self.stdout.write(self.style.SUCCESS(f'Additional staff & students created: {new_school_users}'))

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

        # 7b. Book Copies & Full Movement Chain for School №20 and School №5
        # (lighter catalog per school: first 15 books, 5 copies each, to keep seeding fast)
        other_schools = [
            {
                'school': school20, 'code': '020', 'librarian': librarian_20, 'teacher': teacher_20,
                'students': [student_karim, student_malika], 'library_name': 'Китобхонаи Гимназияи №20',
            },
            {
                'school': school5, 'code': '005', 'librarian': librarian_5, 'teacher': teacher_5,
                'students': [student_5a, student_5b], 'library_name': 'Китобхонаи МТМУ №5',
            },
        ]

        for entry in other_schools:
            school_obj = entry['school']
            code = entry['code']
            lib_user = entry['librarian']
            tch_user = entry['teacher']
            students_list = entry['students']
            library_name = entry['library_name']

            school_copies = []
            for book in created_books[:15]:
                for copy_i in range(1, 6):
                    inv = f'TJ-S{code}-B{book.pk:04d}-{copy_i:05d}'
                    bc = f'BC{code}{book.pk:04d}{copy_i:05d}'
                    copy, created = BookCopy.objects.get_or_create(
                        inventory_number=inv,
                        defaults={
                            'book': book,
                            'barcode': bc,
                            'school': school_obj,
                            'status': BookCopy.Status.AT_LIBRARY,
                        }
                    )
                    if created:
                        BookTransaction.objects.create(
                            book_copy=copy,
                            from_user=None,
                            to_user=lib_user,
                            from_location='Маркази тақсимоти Вазорати маориф',
                            to_location=library_name,
                            transaction_type=BookTransaction.TransactionType.WAREHOUSE_TO_SCHOOL,
                            created_by=super_admin,
                            note='Оприходование тиража 2024 года'
                        )
                    school_copies.append(copy)

            # Librarian -> Teacher -> Student chain for the first two copies per student,
            # including one full round-trip return to demonstrate student -> teacher returns.
            for i, student in enumerate(students_list):
                copy = school_copies[i]
                if copy.status != BookCopy.Status.AT_LIBRARY:
                    continue

                copy.status = BookCopy.Status.ISSUED_TO_TEACHER
                copy.save()
                BookTransaction.objects.create(
                    book_copy=copy,
                    from_user=lib_user,
                    to_user=tch_user,
                    from_location=library_name,
                    to_location=f'Роҳбари синф {tch_user.get_full_name()}',
                    transaction_type=BookTransaction.TransactionType.LIBRARIAN_TO_TEACHER,
                    created_by=lib_user,
                    note='Супоридан ба роҳбари синф'
                )

                copy.status = BookCopy.Status.ISSUED_TO_STUDENT
                copy.save()
                BookTransaction.objects.create(
                    book_copy=copy,
                    from_user=tch_user,
                    to_user=student,
                    from_location=f'Роҳбари синф {tch_user.get_full_name()}',
                    to_location=f'Хонанда {student.get_full_name()}',
                    transaction_type=BookTransaction.TransactionType.TEACHER_TO_STUDENT,
                    created_by=tch_user,
                    note='Супоридан ба хонанда барои соли хониш'
                )

                # First student in each school returns the book to the teacher,
                # demonstrating the "return to teacher" flow (see ReturnFromStudentView).
                if i == 0:
                    copy.status = BookCopy.Status.ISSUED_TO_TEACHER
                    copy.save()
                    BookTransaction.objects.create(
                        book_copy=copy,
                        from_user=student,
                        to_user=tch_user,
                        from_location=f'Хонанда {student.get_full_name()}',
                        to_location=f'Роҳбари синф {tch_user.get_full_name()}',
                        transaction_type=BookTransaction.TransactionType.STUDENT_RETURN,
                        created_by=tch_user,
                        note='Бозгардонидани китоб ба роҳбари синф'
                    )

        # 7c. Bulk book copies for the additional schools. Uses bulk_create
        # instead of the one-by-one get_or_create above, since this generates
        # thousands of rows across 12 schools and needs to stay fast.
        COPIES_PER_BOOK = 4
        total_new_copies = 0
        for school_obj in new_schools:
            code = f'S{school_obj.school_number}'
            lib_user = school_librarians.get(school_obj.pk, super_admin)
            existing_invs = set(
                BookCopy.objects.filter(school=school_obj).values_list('inventory_number', flat=True)
            )
            copies_to_create = []
            for book in created_books:
                for copy_i in range(1, COPIES_PER_BOOK + 1):
                    inv = f'TJ-{code}-B{book.pk:04d}-{copy_i:05d}'
                    if inv in existing_invs:
                        continue
                    copies_to_create.append(BookCopy(
                        book=book,
                        inventory_number=inv,
                        barcode=f'BC{code}{book.pk:04d}{copy_i:05d}',
                        school=school_obj,
                        status=BookCopy.Status.AT_LIBRARY,
                    ))

            if not copies_to_create:
                continue

            created_copies = BookCopy.objects.bulk_create(copies_to_create, batch_size=500)
            BookTransaction.objects.bulk_create([
                BookTransaction(
                    book_copy=copy,
                    from_user=None,
                    to_user=lib_user,
                    from_location='Маркази тақсимоти Вазорати маориф',
                    to_location=f'Китобхонаи мактаби №{school_obj.school_number}',
                    transaction_type=BookTransaction.TransactionType.WAREHOUSE_TO_SCHOOL,
                    created_by=super_admin,
                    note='Оприходование тиража 2024 года',
                )
                for copy in created_copies
            ], batch_size=500)
            total_new_copies += len(created_copies)

        self.stdout.write(self.style.SUCCESS(f'Additional book copies created: {total_new_copies}'))

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
        self.stdout.write(self.style.SUCCESS('--- School №20 (Dushanbe) ---'))
        self.stdout.write(self.style.SUCCESS('   Director:          director_20'))
        self.stdout.write(self.style.SUCCESS('   Librarian:         librarian_20'))
        self.stdout.write(self.style.SUCCESS('   Class Teacher:     teacher_muzaffar'))
        self.stdout.write(self.style.SUCCESS('   Students:          student_karim / student_malika'))
        self.stdout.write(self.style.SUCCESS('--- School №5 (Khujand) ---'))
        self.stdout.write(self.style.SUCCESS('   Director:          director_5'))
        self.stdout.write(self.style.SUCCESS('   Librarian:         librarian_5'))
        self.stdout.write(self.style.SUCCESS('   Class Teacher:     teacher_5'))
        self.stdout.write(self.style.SUCCESS('   Students:          student_5a / student_5b'))
        self.stdout.write(self.style.SUCCESS('=========================================\n'))
