import csv
from django.core.management.base import BaseCommand
from core.models import Sentence

class Command(BaseCommand):
    help = "Load sentences from a CSV file into the database"

    def add_arguments(self, parser):
        parser.add_argument('csv_file', type=str, help="Path to the CSV file")
        parser.add_argument('-C', '--category', type=str, required=True, choices=['beginner', 'intermediate', 'advanced'],
                            help="The category of the sentences (reading, listening, speaking)")
        parser.add_argument('-L', '--level', type=int, required=True, choices=[1, 2, 3, 4, 5],
                            help="The level of the sentences (beginner, intermediate, advanced)")

    def handle(self, *args, **kwargs):
        csv_file = kwargs['csv_file']
        category = kwargs['category']
        level = kwargs['level']

        valid_difficulties = {'easy', 'medium', 'hard'}
        count_created = 0
        count_skipped_duplicates = 0
        count_skipped_invalid_difficulty = 0

        try:
            with open(csv_file, mode='r', encoding='utf-8') as file:
                reader = csv.reader(file)
                rows = list(reader)

                first_row = rows[0]
                has_headers = not any(difficulty in valid_difficulties for difficulty in first_row)

                if has_headers:
                    rows = rows[1:]

                for row in rows:
                    if len(row) < 2:
                        self.stdout.write(self.style.WARNING(f"Skipping row: {row} (insufficient columns)"))
                        continue

                    sentence_text = row[0].strip()
                    difficulty = row[1].strip().lower()

                    if difficulty not in valid_difficulties:
                        count_skipped_invalid_difficulty += 1
                        continue

                    obj, created = Sentence.objects.get_or_create(
                        sentence=sentence_text,
                        defaults={
                            'difficulty': difficulty,
                            'level': level,
                            'category': category,
                        }
                    )
                    if created:
                        count_created += 1
                    else:
                        count_skipped_duplicates += 1

            self.stdout.write(self.style.SUCCESS(
                f"Successfully loaded {count_created} sentences for category '{category}' and level '{level}'."
            ))
            self.stdout.write(self.style.WARNING(
                f"Skipped {count_skipped_duplicates} duplicates."
            ))
            self.stdout.write(self.style.WARNING(
                f"Skipped {count_skipped_invalid_difficulty} sentences due to invalid difficulty levels."
            ))

        except Exception as e:
            self.stdout.write(self.style.ERROR(f"Error: {str(e)}"))