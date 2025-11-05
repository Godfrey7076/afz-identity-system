from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from users.models import Visitor

CustomUser = get_user_model()


class Command(BaseCommand):
    help = 'Create sample data for AFZ Identity System'

    def handle(self, *args, **options):
        self.stdout.write('Creating sample data for AFZ Identity System...')
        self.stdout.write('=' * 50)

        # Create sample users
        users_data = [
            {
                'username': 'admin_afz',
                'email': 'admin@afz.gov.zw',
                'first_name': 'System',
                'last_name': 'Administrator',
                'user_type': 'commander',
                'unit': 'Headquarters',
                'password': 'AfzAdmin2024!'
            },
            {
                'username': 'desk_officer',
                'email': 'desk@afz.gov.zw',
                'first_name': 'John',
                'last_name': 'Moyo',
                'user_type': 'pass_desk',
                'unit': 'Passes and Permits Unit',
                'password': 'DeskOfficer2024!'
            },
            {
                'username': 'security_chief',
                'email': 'security@afz.gov.zw',
                'first_name': 'Sarah',
                'last_name': 'Ndlovu',
                'user_type': 'security_officer',
                'unit': 'Security Division',
                'password': 'SecurityChief2024!'
            }
        ]

        created_count = 0
        for user_data in users_data:
            try:
                # Check if user already exists
                if CustomUser.objects.filter(username=user_data['username']).exists():
                    self.stdout.write(
                        f"ℹ️ User already exists: {user_data['username']}")
                    continue

                # Create new user
                user = CustomUser.objects.create_user(
                    username=user_data['username'],
                    email=user_data['email'],
                    first_name=user_data['first_name'],
                    last_name=user_data['last_name'],
                    user_type=user_data['user_type'],
                    unit=user_data['unit'],
                    is_verified=True
                )
                user.set_password(user_data['password'])
                user.save()

                self.stdout.write(self.style.SUCCESS(
                    f"✅ Created user: {user.username}"))
                self.stdout.write(
                    f"   Security Number: {user.security_number}")
                self.stdout.write(f"   Type: {user.get_user_type_display()}")
                self.stdout.write(f"   Unit: {user.unit}")
                created_count += 1

            except Exception as e:
                self.stdout.write(self.style.ERROR(
                    f"❌ Error creating user {user_data['username']}: {e}"))

        # Display summary
        self.stdout.write("\n" + "=" * 50)
        self.stdout.write("SAMPLE DATA SUMMARY:")
        self.stdout.write(f"Total Users: {CustomUser.objects.count()}")
        self.stdout.write("\nSample login credentials:")
        self.stdout.write("Admin: admin_afz / AfzAdmin2024!")
        self.stdout.write("Desk Officer: desk_officer / DeskOfficer2024!")
        self.stdout.write(
            "Security Chief: security_chief / SecurityChief2024!")
        self.stdout.write(self.style.SUCCESS(
            "\nSample data creation completed! ✅"))
