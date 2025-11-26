from django.core.management.base import BaseCommand
from tickets.models import Corpus, Ticket, User

class Command(BaseCommand):
    help = 'Migrate existing corpus strings to Corpus model'

    def handle(self, *args, **options):
        # Создаем корпуса
        corpuses_data = [
            {'name': 'Главный корпус', 'number': 0},
            {'name': 'Корпус 1', 'number': 1},
            {'name': 'Корпус 2', 'number': 2},
            {'name': 'Корпус 3', 'number': 3},
            {'name': 'Корпус 4', 'number': 4},
            {'name': 'Корпус 5', 'number': 5},
            {'name': 'Корпус 6', 'number': 6},
            {'name': 'Корпус 7', 'number': 7},
            {'name': 'Корпус 8', 'number': 8},
            {'name': 'Корпус 9', 'number': 9},
        ]
        
        corpus_map = {}
        for data in corpuses_data:
            corpus, created = Corpus.objects.get_or_create(
                name=data['name'],
                defaults={'number': data['number']}
            )
            corpus_map[data['name']] = corpus
            if created:
                self.stdout.write(self.style.SUCCESS(f'Created corpus: {corpus}'))
        
        # Мигрируем тикеты (если есть старые данные)
        # Это нужно только если есть данные до миграции
        # В новом проекте это не нужно, но оставим для совместимости
        
        self.stdout.write(self.style.SUCCESS('Corpus migration completed!'))

