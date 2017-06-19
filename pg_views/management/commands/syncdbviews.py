from optparse import make_option

from django.core.management.base import BaseCommand
from django.db import connection

from pg_views.loading import get_sql_model_views
from pg_views.compatibility import CompatibilityBaseCommand


class Command(CompatibilityBaseCommand):

    help = 'Create DB views and add permissions to read it to the the DB view user.'

    def add_arguments(self, parser):
        super(Command, self).add_arguments(parser)
        parser.add_argument(
            '--database_view_username', action='store', dest='database_view_username',
            default=None,
            help='Specifies the database view user to use. If is not set the permissions will not be set.')

    def _drop_view(self, model_view):
        self.stdout.write('Drop view "{view_db_name}"'.format(
            view_db_name=model_view.get_name()
        ))
        connection.cursor().execute(model_view.get_sql_drop_view())

    def _create_view(self, model_view):
        self.stdout.write('Create view "{view_db_name}"'.format(
            view_db_name=model_view.get_name()
        ))
        connection.cursor().execute(model_view.get_sql_create_view())

    def _grand_user_permissions(self, model_view, username):
        if username:
            self.stdout.write('Grand read permission on "{view_db_name}" to "{username}";'.format(
                username=username,
                view_db_name=model_view.get_name()
            ))
            connection.cursor().execute('GRANT SELECT ON "{view_db_name}" TO "{username}";'.format(
                username=username,
                view_db_name=model_view.get_name()
            ))

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
