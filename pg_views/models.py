import sys

from django.utils import six
from django.utils.datastructures import SortedDict

from .loading import register_sql_model_view


class ModelViewBase(type):

    def __new__(cls, *args, **kwargs):
        name, _, attrs = args
        abstract = attrs.pop('abstract', False)
        super_new = super(ModelViewBase, cls).__new__
        new_class = super_new(cls, *args, **kwargs)
        model_module = sys.modules[new_class.__module__]
        app_label = model_module.__name__.split('.')[-2]
        if name != 'NewBase' and not abstract:
            register_sql_model_view(app_label, new_class)
        return new_class


class ModelView(six.with_metaclass(ModelViewBase)):
    abstract = True
    model = None
    view_name = None
    upper_names = True
    exclude = ()
    column_name_mapping = {}

    def get_column_name(self, model_column_name):
        column_name = self.column_name_mapping.get(model_column_name, model_column_name)
        return self.upper_names and column_name.upper() or column_name

    def get_columns(self):
        result = SortedDict()
        for field in self.model._meta.fields:
            attname, column = field.get_attname_column()
            if attname not in self.exclude:
                result[self.get_column_name(column)] = column
        return result

    def get_name(self):
        name = self.view_name or '%s_view' % self.model._meta.db_table
        return self.upper_names and name.upper() or name
