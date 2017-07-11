from django.conf import settings
from django.core.management.base import BaseCommand
from django.db import connection


class Command(BaseCommand):

    help = 'Drop all DB views.'

    def handle(self, **options):
        cursor = connection.cursor()
        cursor.execute('''SELECT table_name
                          FROM information_schema.views
                          WHERE table_schema NOT IN ('pg_catalog', 'information_schema')
                          AND table_name !~ '^pg_';''')
        count_dropped_views = 0
        for columns in cursor.fetchall():
            view_name = columns[0]
            if view_name not in getattr(settings, 'PG_VIEWS_IGNORE', {}):
                self.stdout.write('Drop view {}'.format(view_name))
                cursor.execute('DROP VIEW "{}";'.format(view_name))
                count_dropped_views += 1
        if count_dropped_views == 0:
            self.stdout.write('No view was dropped')
