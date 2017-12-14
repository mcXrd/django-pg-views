import sys

from collections import OrderedDict

from django.utils import six
from django.db import connection, models
from django.utils.translation import ugettext

from .loading import register_sql_model_view, get_sql_model_view


class DBViewBase(type):

    def __new__(cls, *args, **kwargs):
        name, _, attrs = args
        abstract = attrs.pop('abstract', False)
        super_new = super(DBViewBase, cls).__new__
        new_class = super_new(cls, *args, **kwargs)
        model_module = sys.modules[new_class.__module__]
        app_label = model_module.__name__.split('.')[-2]
        if name != 'NewBase' and not abstract:
            register_sql_model_view(app_label, new_class)
        return new_class


class DBView(six.with_metaclass(DBViewBase)):
    abstract = True
    view_name = None
    upper_names = True

    def get_columns(self):
        return OrderedDict()

    def get_name(self):
        return self.upper_names and self.view_name.upper() or self.view_name

    def get_condition(self):
        return None


class ModelDBView(DBView):

    abstract = True
    model = None
    exclude = ()
    fields = None
    column_name_mapping = {}

    def get_field_db_type(self, field):
        field_db_type = field.db_type(connection).split('CHECK')[0].strip()
        return 'integer' if field_db_type == 'serial' else field_db_type

    def get_column_name(self, model_column_name):
        column_name = self.column_name_mapping.get(model_column_name, model_column_name)
        return self.upper_names and column_name.upper() or column_name
    
    def get_fields(self):
        return self.model._meta.fields

    @property
    def verbose_name(self):
        return self.model._meta.verbose_name

    def get_columns(self):
        result = super(ModelDBView, self).get_columns()
        for field in self.get_fields():
            attname, column = field.get_attname_column()
            if attname not in self.exclude and (self.fields is None or field.name in self.fields):
                verbose_name = field.verbose_name
                if isinstance(field, models.ForeignKey) and get_sql_model_view(field.rel.to):
                    verbose_name = '{} ({} {})'.format(verbose_name, ugettext('foreign key to view'),
                                                       get_sql_model_view(field.rel.to)().get_name())
                result[self.get_column_name(column)] = (column, verbose_name, self.get_field_db_type(field))
        return result
    
    @property
    def db_table(self):
        return self.model._meta.db_table

    def get_name(self):
        name = self.view_name or '%s_view' % self.db_table
        return self.upper_names and name.upper() or name

    def get_sql_view_columns(self):
        return ', '.join([
            '{} AS "{}"'.format(column_from, column_to)
            for column_from, column_to in [(value[0], key) for key, value in self.get_columns().items()]
        ])

    def get_sql_parent_tables(self, model):
        return ''.join([
            ' INNER JOIN "{ptr_model}" ON ({join_condition}){sql_ptr_parent_tables}'.format(
                ptr_model=ptr_model._meta.db_table,
                join_condition=' AND '.join([
                    '"{model}"."{model_join_column}" = "{ptr_model}"."{ptr_model_join_column}"'.format(
                        model=model._meta.db_table,
                        ptr_model=ptr_model._meta.db_table,
                        model_join_column=model_join_column,
                        ptr_model_join_column=ptr_model_join_column
                    ) for (ptr_model_join_column, model_join_column) in field.get_reverse_joining_columns()
                ]),
                sql_ptr_parent_tables=self.get_sql_parent_tables(ptr_model)
            ) for ptr_model, field in model._meta.parents.items()
        ])

    def get_sql_from_tables(self):
        return '"{table_name}"{sql_parent_tables}'.format(
            table_name=self.db_table,
            sql_parent_tables=self.get_sql_parent_tables(self.model)
        )

    def get_sql_create_view(self):
        condition = self.get_condition()
        return 'CREATE VIEW "{view_name}" AS SELECT {columns} FROM {from_tables}{where};'.format(
            view_name=self.get_name(),
            columns=self.get_sql_view_columns(),
            from_tables=self.get_sql_from_tables(),
            where=' WHERE {}'.format(condition) if condition else ''
        )

    def get_sql_drop_view(self):
        return 'DROP VIEW IF EXISTS "{view_name}"'.format(view_name=self.get_name())


class ManyToManyDBView(ModelDBView):

    abstract = True
    model = None
    m2m_field = None
    _verbose_name = None

    def get_m2m_field(self):
        return getattr(self.model, self.m2m_field)

    @property
    def db_table(self):
        return self.get_m2m_field().through._meta.db_table

    @property
    def verbose_name(self):
        return _verbose_name or self.get_m2m_field().through._meta.verbose_name

    @verbose_name.setter
    def verbose_name(self, value):
        self._verbose_name = value

    def get_fields(self):
        return self.get_m2m_field().through._meta.fields

    def get_sql_from_tables(self):
        return self.db_table
