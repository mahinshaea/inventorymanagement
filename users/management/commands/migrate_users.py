from django.core.management.base import BaseCommand
from django.db import connection

class Command(BaseCommand):
    help = 'Migrate users from hello_app to users app'

    def handle(self, *args, **options):
        try:
            with connection.cursor() as cursor:
                # Copy data from hello_app_user to users_user
                cursor.execute("""
                    INSERT INTO users_user 
                    (name, password, email, role, created_at, updated_at)
                    SELECT name, password, email, role, created_at, updated_at 
                    FROM hello_app_user
                """)
                
                # Get count of migrated records
                cursor.execute("SELECT COUNT(*) FROM users_user")
                count = cursor.fetchone()[0]
                
                self.stdout.write(
                    self.style.SUCCESS(f'Successfully migrated {count} users')
                )
        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f'Error during migration: {str(e)}')
            )