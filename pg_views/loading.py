from collections import OrderedDict

from django.conf import settings
from django.utils.importlib import import_module
from django.utils.encoding import force_text


class App(object):

    def __init__(self):
        self.model_sql_views = set()


class ModelSQLViewsLoader(object):

    def __init__(self):
        self.apps = OrderedDict()

    def register_sql_model_view(self, app_label, model_sql_view):
        app = self.apps.get(app_label, App())
        app.model_sql_views.add(model_sql_view)
        self.apps[app_label] = app

    def _init_apps(self):
        for app in settings.INSTALLED_APPS:
            try:
                import_module('%s.models' % app)
            except ImportError as ex:
                if force_text(ex) != 'No module named models':
                    raise ex

    def get_sql_model_views(self):
        self._init_apps()

        for app in self.apps.values():
            for sql_model_view in app.model_sql_views:
                yield sql_model_view

loader = ModelSQLViewsLoader()
register_sql_model_view = loader.register_sql_model_view
get_sql_model_views = loader.get_sql_model_views
