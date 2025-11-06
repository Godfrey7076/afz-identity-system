from django.core.management.base import BaseCommand
import random
from datetime import date, timedelta
from django.utils import timezone
from identity_verification.models import Person, IDRecord, SecurityLog, SystemSettings


class Command(BaseCommand):
    help = 'Generate sample data for Air Force Zimbabwe Identity System'

    def generate_security_number(self):
        """Generate AFZ security number format: AFZ-XXXX-XXXX-XXXX"""
        return f"AFZ-{random.randint(1000, 9999)}-{random.randint(1000, 9999)}-{random.randint(1000, 9999)}"

    def generate_military_id(self):
        """Generate military ID format: AFZ-XX-XXXX"""
        return f"AFZ-{random.randint(10, 99)}-{random.randint(1000, 9999)}"

    def handle(self, *args, **options):
        self.stdout.write(
            "🚀 Creating sample data for Air Force Zimbabwe Identity System...")

        # Create system settings if they don't exist
        settings, created = SystemSettings.objects.get_or_create(
            id=1,
            defaults={
                'system_name': 'Air Force Zimbabwe Identity Management System',
                'max_login_attempts': 3,
                'session_timeout': 30,
                'face_match_threshold': 0.8
            }
        )

        # Sample personnel data with specific wings and sections
        personnel_data = [
            # Flying Wing - Higher ranks
            {
                'first_name': 'Tendai',
                'last_name': 'Moyo',
                'rank': 'Squadron Leader',
                'unit': 'Flying Wing',
                'date_of_birth': date(1978, 5, 15),
                'service_number': 'AFZ-01-1001'
            },
            {
                'first_name': 'Anesu',
                'last_name': 'Chikowore',
                'rank': 'Flight Lieutenant',
                'unit': 'Flying Wing',
                'date_of_birth': date(1982, 8, 22),
                'service_number': 'AFZ-02-2001'
            },
            {
                'first_name': 'Farai',
                'last_name': 'Ndlovu',
                'rank': 'Air Lieutenant',
                'unit': 'Flying Wing',
                'date_of_birth': date(1985, 3, 10),
                'service_number': 'AFZ-03-3001'
            },
            {
                'first_name': 'Rumbidzai',
                'last_name': 'Mpofu',
                'rank': 'Master Sergeant',
                'unit': 'Flying Wing',
                'date_of_birth': date(1988, 11, 30),
                'service_number': 'AFZ-04-4001'
            },
            {
                'first_name': 'Tatenda',
                'last_name': 'Mutungira',
                'rank': 'Flight Sergeant',
                'unit': 'Flying Wing',
                'date_of_birth': date(1990, 7, 18),
                'service_number': 'AFZ-05-5001'
            },
            {
                'first_name': 'Munyaradzi',
                'last_name': 'Mandirowa',
                'rank': 'Sergeant',
                'unit': 'Flying Wing',
                'date_of_birth': date(1993, 8, 19),
                'service_number': 'AFZ-06-6001'
            },
            # Regiment Dog Section
            {
                'first_name': 'Chiedza',
                'last_name': 'Zhou',
                'rank': 'Flight Lieutenant',
                'unit': 'Regiment Dog Section',
                'date_of_birth': date(1984, 12, 5),
                'service_number': 'AFZ-07-7001'
            },
            {
                'first_name': 'Kudakwashe',
                'last_name': 'Mukanya',
                'rank': 'Air Lieutenant',
                'unit': 'Regiment Dog Section',
                'date_of_birth': date(1987, 4, 25),
                'service_number': 'AFZ-08-8001'
            },
            {
                'first_name': 'Nyasha',
                'last_name': 'Gumbo',
                'rank': 'Master Sergeant',
                'unit': 'Regiment Dog Section',
                'date_of_birth': date(1989, 9, 14),
                'service_number': 'AFZ-09-9001'
            },
            {
                'first_name': 'Rutendo',
                'last_name': 'Mazivisa',
                'rank': 'Flight Sergeant',
                'unit': 'Regiment Dog Section',
                'date_of_birth': date(1992, 1, 25),
                'service_number': 'AFZ-10-1001'
            },
            {
                'first_name': 'Blessing',
                'last_name': 'Marufu',
                'rank': 'Sergeant',
                'unit': 'Regiment Dog Section',
                'date_of_birth': date(1994, 7, 12),
                'service_number': 'AFZ-11-1101'
            },
            # Provost Section
            {
                'first_name': 'Tawanda',
                'last_name': 'Sibanda',
                'rank': 'Master Sergeant',
                'unit': 'Provost Section',
                'date_of_birth': date(1986, 6, 8),
                'service_number': 'AFZ-12-1201'
            },
            {
                'first_name': 'Shamiso',
                'last_name': 'Machingauta',
                'rank': 'Flight Sergeant',
                'unit': 'Provost Section',
                'date_of_birth': date(1989, 2, 28),
                'service_number': 'AFZ-13-1301'
            },
            {
                'first_name': 'Tinashe',
                'last_name': 'Mupfumi',
                'rank': 'Sergeant',
                'unit': 'Provost Section',
                'date_of_birth': date(1991, 6, 30),
                'service_number': 'AFZ-14-1401'
            },
            {
                'first_name': 'Prudence',
                'last_name': 'Chigumba',
                'rank': 'Sergeant',
                'unit': 'Provost Section',
                'date_of_birth': date(1993, 11, 3),
                'service_number': 'AFZ-15-1501'
            },
            # Radios Section
            {
                'first_name': 'Yolanda',
                'last_name': 'Chiweshe',
                'rank': 'Air Lieutenant',
                'unit': 'Radios Section',
                'date_of_birth': date(1988, 3, 14),
                'service_number': 'AFZ-16-1601'
            },
            {
                'first_name': 'Blessing',
                'last_name': 'Mangwiro',
                'rank': 'Master Sergeant',
                'unit': 'Radios Section',
                'date_of_birth': date(1990, 5, 22),
                'service_number': 'AFZ-17-1701'
            },
            {
                'first_name': 'Farai',
                'last_name': 'Mapani',
                'rank': 'Flight Sergeant',
                'unit': 'Radios Section',
                'date_of_birth': date(1992, 9, 8),
                'service_number': 'AFZ-18-1801'
            },
            {
                'first_name': 'Rudo',
                'last_name': 'Mazango',
                'rank': 'Sergeant',
                'unit': 'Radios Section',
                'date_of_birth': date(1995, 12, 17),
                'service_number': 'AFZ-19-1901'
            },
            {
                'first_name': 'Tendai',
                'last_name': 'Mukonori',
                'rank': 'Sergeant',
                'unit': 'Radios Section',
                'date_of_birth': date(1996, 4, 3),
                'service_number': 'AFZ-20-2001'
            }
        ]

        # Create personnel and ID records
        for i, data in enumerate(personnel_data):
            # Create or get person
            person, created = Person.objects.get_or_create(
                first_name=data['first_name'],
                last_name=data['last_name'],
                defaults={
                    'rank': data['rank'],
                    'unit': data['unit'],
                    'date_of_birth': data['date_of_birth'],
                    'service_number': data['service_number'],
                    'security_clearance': random.choice(['TOP SECRET', 'SECRET', 'CONFIDENTIAL', 'RESTRICTED']),
                    'status': 'ACTIVE'
                }
            )

            if created:
                # Create ID record with security number
                id_record = IDRecord.objects.create(
                    person=person,
                    security_number=self.generate_security_number(),
                    issue_date=timezone.now() - timedelta(days=random.randint(30, 365)),
                    expiry_date=timezone.now() + timedelta(days=random.randint(180, 730)),
                    id_type=random.choice(
                        ['MILITARY_ID', 'ACCESS_CARD', 'VISITOR_PASS']),
                    status=random.choice(
                        ['ACTIVE', 'ACTIVE', 'ACTIVE', 'SUSPENDED'])  # Mostly active
                )

                self.stdout.write(
                    self.style.SUCCESS(
                        f"✅ Created {person.rank} {person.first_name} {person.last_name}")
                )
                self.stdout.write(f"   Unit: {person.unit}")
                self.stdout.write(
                    f"   Service Number: {person.service_number}")
                self.stdout.write(
                    f"   Security Number: {id_record.security_number}")
                self.stdout.write(
                    f"   Security Clearance: {person.security_clearance}")
                self.stdout.write("")

        # Create sample security logs
        actions = ['LOGIN_ATTEMPT', 'ACCESS_GRANTED', 'ACCESS_DENIED', 'ID_ISSUED',
                   'ID_REVOKED', 'FACE_VERIFICATION_SUCCESS', 'FACE_VERIFICATION_FAILED']
        persons = Person.objects.all()

        for _ in range(60):
            person = random.choice(persons)
            SecurityLog.objects.create(
                person=person,
                action=random.choice(actions),
                details=f"Security event - {random.choice(['Base access', 'System login', 'ID verification', 'Area entry'])} for {person.rank} {person.last_name} from {person.unit}",
                ip_address=f"192.168.1.{random.randint(1, 255)}",
                user_agent="Mozilla/5.0 (Sample User Agent)",
                timestamp=timezone.now() - timedelta(hours=random.randint(1, 720))
            )

        # Print summary by unit and rank
        self.stdout.write(
            self.style.SUCCESS("\n🎉 Sample data creation completed!")
        )

        self.stdout.write("\n📊 SUMMARY BY UNIT:")
        units = Person.objects.values_list('unit', flat=True).distinct()
        for unit in units:
            count = Person.objects.filter(unit=unit).count()
            self.stdout.write(f"   {unit}: {count} personnel")

        self.stdout.write("\n🎖️  RANK DISTRIBUTION:")
        ranks = Person.objects.values_list('rank', flat=True).distinct()
        for rank in sorted(ranks):
            count = Person.objects.filter(rank=rank).count()
            self.stdout.write(f"   {rank}: {count} personnel")

        self.stdout.write("\n📊 OVERALL STATISTICS:")
        self.stdout.write(
            f"   Total Personnel: {Person.objects.count()} records")
        self.stdout.write(
            f"   Total ID Records: {IDRecord.objects.count()} records")
        self.stdout.write(
            f"   Total Security Logs: {SecurityLog.objects.count()} logs")
        self.stdout.write(
            f"\n🔐 Security numbers follow: AFZ-XXXX-XXXX-XXXX format")
        self.stdout.write(f"🎖️  Military IDs follow: AFZ-XX-XXXX format")
