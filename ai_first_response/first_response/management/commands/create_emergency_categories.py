from django.core.management.base import BaseCommand
from first_response.models import EmergencyCategory

class Command(BaseCommand):
    help = 'Create default emergency categories'

    def handle(self, *args, **options):
        categories = [
            {
                'title': 'Earthquake',
                'quick_message': 'There was an earthquake, I need help and safety instructions',
                'icon': '🏠',
                'css_class': 'btn-outline-danger',
                'order': 1
            },
            {
                'title': 'Medical Emergency',
                'quick_message': 'I need medical help, someone is injured or having a medical emergency',
                'icon': '🚑',
                'css_class': 'btn-outline-danger',
                'order': 2
            },
            {
                'title': 'Fire Emergency',
                'quick_message': 'There is a fire nearby, I need evacuation instructions',
                'icon': '🔥',
                'css_class': 'btn-outline-warning',
                'order': 3
            },
            {
                'title': 'Flood Emergency',
                'quick_message': 'There is flooding in my area, I need safety instructions',
                'icon': '🌊',
                'css_class': 'btn-outline-info',
                'order': 4
            },
            {
                'title': 'Police Emergency',
                'quick_message': 'I need police assistance, there is a security emergency',
                'icon': '👮',
                'css_class': 'btn-outline-primary',
                'order': 5
            },
            {
                'title': 'Weather Emergency',
                'quick_message': 'There is severe weather (storm, tornado, etc.) in my area',
                'icon': '🌩️',
                'css_class': 'btn-outline-secondary',
                'order': 6
            }
        ]
        
        created_count = 0
        for cat_data in categories:
            category, created = EmergencyCategory.objects.get_or_create(
                title=cat_data['title'],
                defaults=cat_data
            )
            if created:
                created_count += 1
                self.stdout.write(
                    self.style.SUCCESS(f'Created category: {category.icon} {category.title}')
                )
            else:
                self.stdout.write(f'Category already exists: {category.icon} {category.title}')
        
        self.stdout.write(
            self.style.SUCCESS(f'Successfully created {created_count} new emergency categories')
        )
