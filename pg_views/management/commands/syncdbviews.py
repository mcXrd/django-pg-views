from optparse import make_option

from django.core.management.base import BaseCommand
from django.db import connection

from pg_views.loading import get_sql_model_views


class Command(BaseCommand):

    option_list = BaseCommand.option_list + (
        make_option('--database_view_username', action='store', dest='database_view_username',
            default=None,
            help='Specifies the database view user to use. If is not set the permissions will not be set.'),
    )
    help = 'Create DB views and add permissions to read it to the the DB view user.'

    def _get_view_columns(self, model_view):
        return [(value, key) for key, value in model_view.get_columns().items()]

    def _drop_view(self, model_view):
        self.stdout.write('Drop view "%(view_db_name)s"' % {
            'view_db_name': model_view.get_name()
        })
        connection.cursor().execute('DROP VIEW IF EXISTS "%(view_name)s"' % {'view_name': model_view.get_name()})

    def _create_view(self, model_view):
        self.stdout.write('Create view "%(view_db_name)s"' % {
            'view_db_name': model_view.get_name()
        })
        connection.cursor().execute('CREATE VIEW "%(view_name)s" AS SELECT %(columns)s FROM "%(table_name)s";' % {
                'view_name': model_view.get_name(),
                'columns': ', '.join(['%s AS "%s"' % (column_from, column_to)
                                      for column_from, column_to in self._get_view_columns(model_view)]),
                'table_name': model_view.model._meta.db_table,
        })

    def _grand_user_permissions(self, model_view, username):
        if username:
            self.stdout.write('Grand read permission on "%(view_db_name)s" to "%(username)s";' % {
                'username': username,
                'view_db_name': model_view.get_name()
            })
            connection.cursor().execute('GRANT SELECT ON "%(view_db_name)s" TO "%(username)s";' % {
                'username': username,
                'view_db_name': model_view.get_name()
            })

    def _create_db_view(self, model_view_class, **options):
        model_view = model_view_class()
        self._drop_view(model_view)
        self._create_view(model_view)
        self._grand_user_permissions(model_view, options.get('database_view_username'))

    def _create_db_views(self, **options):
        self.stdout.write('Sync DB Views')
        for model_view_class in get_sql_model_views():
            self._create_db_view(model_view_class, **options)

    def handle(self, *args, **options):
        self._create_db_views(**options)
