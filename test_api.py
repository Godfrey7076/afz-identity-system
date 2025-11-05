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


def test_database():
    print("Testing Database Connection...")

    try:
        from django.contrib.auth import get_user_model
        from users.models import Visitor

        User = get_user_model()
        user_count = User.objects.count()
        visitor_count = Visitor.objects.count()

        print(f"✅ Users in database: {user_count}")
        print(f"✅ Visitors in database: {visitor_count}")

        # List sample users
        print("\nSample Users:")
        for user in User.objects.all()[:5]:
            print(
                f"  - {user.username} ({user.get_user_type_display()}) - {user.security_number}")

        return True

    except Exception as e:
        print(f"❌ Database test failed: {e}")
        return False


def test_models():
    print("\nTesting Models...")

    try:
        from users.models import CustomUser

        # Test security number generation
        test_user = CustomUser.objects.create_user(
            username='test_user',
            email='test@afz.gov.zw',
            password='testpass123',
            first_name='Test',
            last_name='User',
            user_type='pass_desk'
        )

        print(
            f"✅ User created with auto security number: {test_user.security_number}")

        # Clean up
        test_user.delete()
        print("✅ Test user cleaned up")

        return True

    except Exception as e:
        print(f"❌ Model test failed: {e}")
        return False


if __name__ == "__main__":
    print("AFZ Identity System - Database Tests")
    print("=" * 40)

    db_success = test_database()
    model_success = test_models()

    print("\n" + "=" * 40)
    if db_success and model_success:
        print("✅ All tests passed! System is ready.")
    else:
        print("⚠️ Some tests failed. Check the errors above.")
