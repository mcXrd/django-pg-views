from collections import OrderedDict

import six

from importlib import import_module

from django.utils.encoding import force_text
from django.apps import apps


class App(object):

    def __init__(self):
        self.model_sql_views = []

    def add(self, view):
        if view not in self.model_sql_views:
            self.model_sql_views.append(view)


class ModelSQLViewsLoader(object):

    def __init__(self):
        self.apps = OrderedDict()

    def register_sql_model_view(self, app_label, model_sql_view):
        app = self.apps.get(app_label, App())
        app.add(model_sql_view)
        self.apps[app_label] = app

    def _init_apps(self):
        for app in apps.get_app_configs():
            try:
                import_module('{}.models'.format(app.name))
            except ImportError as ex:
                if ((six.PY2 and force_text(ex) != 'No module named models') or
                        (six.PY3 and force_text(ex) != 'No module named \'{}.models\''.format(app.name))):
                    raise ex

    def get_sql_model_views(self):
        self._init_apps()

        for app in self.apps.values():
            for sql_model_view in app.model_sql_views:
                yield sql_model_view

    def get_sql_model_view(self, model):
        self._init_apps()

        for app in self.apps.values():
            for sql_model_view in app.model_sql_views:
                if sql_model_view.model == model:
                    return sql_model_view
        return None


loader = ModelSQLViewsLoader()
register_sql_model_view = loader.register_sql_model_view
get_sql_model_views = loader.get_sql_model_views
get_sql_model_view = loader.get_sql_model_view
