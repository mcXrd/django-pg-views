from django.apps import apps
from django.conf import settings
from django.core.management.base import BaseCommand
from pg_views.loading import get_sql_model_views


class Command(BaseCommand):

    def handle(self, **options):
        model_db_names = {model._meta.db_table for model in apps.get_models()}
        models_with_db_view_db_names = {view.model._meta.db_table for view in get_sql_model_views()}
        excluded_db_names = set(getattr(settings, 'DEACTIVATED_VIEWS', ()))

        missing_db_names = model_db_names - excluded_db_names - models_with_db_view_db_names

        if missing_db_names:
            self.stderr.write('Missing db views for models: {}'.format(', '.join((str(model)
                                                                                  for model in apps.get_models() if model._meta.db_table in missing_db_names))))
        else:
            self.stdout.write('All models has db views')
