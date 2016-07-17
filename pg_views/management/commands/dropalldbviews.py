from django.core.management.base import BaseCommand
from django.db import connection


class Command(BaseCommand):

    help = 'Drop all DB views.'

    def handle(self, **options):
        cursor = connection.cursor()
        cursor.execute('''SELECT 'DROP VIEW "' || table_name || '";'
                          FROM information_schema.views
                          WHERE table_schema NOT IN ('pg_catalog', 'information_schema')
                          AND table_name !~ '^pg_';''')
        for drop_command in cursor.fetchall():
            self.stdout.write('Drop view %s' % drop_command[0].split('"')[1])
            cursor.execute(drop_command[0])
        else:
            self.stdout.write('No view was dropped')
