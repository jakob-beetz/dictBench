from django.core.management.base import BaseCommand, CommandError
from properties.iso16757_import import parse_and_import
from dictionaries.models import PropertyDictionary
from django.contrib.auth import get_user_model


class Command(BaseCommand):
    help = 'Import ISO 16757 CSV into properties'

    def add_arguments(self, parser):
        parser.add_argument('csvfile', type=str)
        parser.add_argument('--dictionary', required=True, help='Dictionary PK to attach properties to')
        parser.add_argument('--user', required=False, help='username for created_by/updated_by')

    def handle(self, *args, **options):
        csvpath = options['csvfile']
        dict_pk = options['dictionary']
        username = options.get('user')

        User = get_user_model()
        user = None
        if username:
            user = User.objects.filter(username=username).first()
        if not user:
            user = User.objects.filter(is_superuser=True).first()
        if not user:
            raise CommandError('No suitable user found for import')

        try:
            dictionary = PropertyDictionary.objects.get(pk=dict_pk)
        except PropertyDictionary.DoesNotExist:
            raise CommandError('Dictionary not found')

        with open(csvpath, 'rb') as fh:
            stats = parse_and_import(fh, dictionary, user)

        self.stdout.write(self.style.SUCCESS(f'Import finished: {stats}'))
