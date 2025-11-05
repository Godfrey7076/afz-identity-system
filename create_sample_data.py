from users.models import Visitor
from django.contrib.auth import get_user_model
import os
import sys
import django

# Add the project directory to Python path
project_path = os.path.dirname(os.path.abspath(__file__))
sys.path.append(project_path)

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'afz_core.settings')

try:
    django.setup()
    print("✅ Django setup successful")
except Exception as e:
    print(f"❌ Django setup failed: {e}")
    sys.exit(1)


CustomUser = get_user_model()


def create_sample_users():
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
                print(f"ℹ️ User already exists: {user_data['username']}")
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

            print(f"✅ Created user: {user.username}")
            print(f"   Security Number: {user.security_number}")
            print(f"   Type: {user.get_user_type_display()}")
            print(f"   Unit: {user.unit}")
            created_count += 1

        except Exception as e:
            print(f"❌ Error creating user {user_data['username']}: {e}")

    return created_count


def main():
    print("Creating sample data for AFZ Identity System...")
    print("=" * 50)

    # Create sample users
    user_count = create_sample_users()

    # Display summary
    print("\n" + "=" * 50)
    print("SAMPLE DATA SUMMARY:")
    print(f"Total Users: {CustomUser.objects.count()}")
    print("\nSample login credentials:")
    print("Admin: admin_afz / AfzAdmin2024!")
    print("Desk Officer: desk_officer / DeskOfficer2024!")
    print("Security Chief: security_chief / SecurityChief2024!")
    print("\nSample data creation completed! ✅")


if __name__ == "__main__":
    main()
