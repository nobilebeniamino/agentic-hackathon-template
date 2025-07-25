from django.core.management.base import BaseCommand
from first_response.models import EmergencyCategory

class Command(BaseCommand):
    help = 'Create multilingual emergency categories'

    def handle(self, *args, **options):
        # Clear existing categories first
        EmergencyCategory.objects.all().delete()
        self.stdout.write(self.style.WARNING('Cleared existing categories'))
        
        categories = [
            {
                'title_en': 'Earthquake',
                'title_it': 'Terremoto',
                'quick_message_en': 'There was an earthquake, I need help and safety instructions',
                'quick_message_it': 'C\'è stato un terremoto, ho bisogno di aiuto e istruzioni di sicurezza',
                'icon': '🏠',
                'css_class': 'btn-outline-danger',
                'order': 1
            },
            {
                'title_en': 'Medical Emergency',
                'title_it': 'Emergenza Medica',
                'quick_message_en': 'I need medical help, someone is injured or having a medical emergency',
                'quick_message_it': 'Ho bisogno di aiuto medico, qualcuno è ferito o ha un\'emergenza medica',
                'icon': '🚑',
                'css_class': 'btn-outline-danger',
                'order': 2
            },
            {
                'title_en': 'Fire Emergency',
                'title_it': 'Emergenza Incendio',
                'quick_message_en': 'There is a fire nearby, I need evacuation instructions',
                'quick_message_it': 'C\'è un incendio nelle vicinanze, ho bisogno di istruzioni per l\'evacuazione',
                'icon': '🔥',
                'css_class': 'btn-outline-warning',
                'order': 3
            },
            {
                'title_en': 'Flood Emergency',
                'title_it': 'Emergenza Alluvione',
                'quick_message_en': 'There is flooding in my area, I need safety instructions',
                'quick_message_it': 'C\'è un\'alluvione nella mia zona, ho bisogno di istruzioni di sicurezza',
                'icon': '🌊',
                'css_class': 'btn-outline-info',
                'order': 4
            },
            {
                'title_en': 'Police Emergency',
                'title_it': 'Emergenza Polizia',
                'quick_message_en': 'I need police assistance, there is a security emergency',
                'quick_message_it': 'Ho bisogno dell\'assistenza della polizia, c\'è un\'emergenza di sicurezza',
                'icon': '👮',
                'css_class': 'btn-outline-primary',
                'order': 5
            },
            {
                'title_en': 'Weather Emergency',
                'title_it': 'Emergenza Meteo',
                'quick_message_en': 'There is severe weather (storm, tornado, etc.) in my area',
                'quick_message_it': 'C\'è maltempo grave (tempesta, tornado, ecc.) nella mia zona',
                'icon': '🌩️',
                'css_class': 'btn-outline-secondary',
                'order': 6
            }
        ]
        
        created_count = 0
        # Create English versions
        for cat_data in categories:
            category = EmergencyCategory.objects.create(
                title=cat_data['title_en'],
                quick_message=cat_data['quick_message_en'],
                icon=cat_data['icon'],
                css_class=cat_data['css_class'],
                order=cat_data['order']
            )
            created_count += 1
            self.stdout.write(
                self.style.SUCCESS(f'Created EN category: {category.icon} {category.title}')
            )
        
        # Create Italian versions with higher order numbers
        for cat_data in categories:
            category = EmergencyCategory.objects.create(
                title=cat_data['title_it'],
                quick_message=cat_data['quick_message_it'],
                icon=cat_data['icon'],
                css_class=cat_data['css_class'],
                order=cat_data['order'] + 100  # Italian categories have order 101-106
            )
            created_count += 1
            self.stdout.write(
                self.style.SUCCESS(f'Created IT category: {category.icon} {category.title}')
            )
        
        self.stdout.write(
            self.style.SUCCESS(f'Successfully created {created_count} multilingual emergency categories')
        )
