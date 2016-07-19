import os

import re

from copy import deepcopy

from django.conf import settings
from django.core.management.base import BaseCommand

from chamber.utils.decorators import translation_activate_block

from pg_views.management.commands import CommandMixin
from pg_views.loading import get_sql_model_views


class Command(CommandMixin, BaseCommand):

    help = 'Generate db views migration.'

    migration_file_regex = re.compile(r'^\d{4}\.py$')

    def init_view_migrations_root(self):
        if not os.path.exists(settings.PG_VIEWS_MIGRATIONS_ROOT):
            os.makedirs(settings.PG_VIEWS_MIGRATIONS_ROOT)

        if '__index__.py' not in os.listdir(settings.PG_VIEWS_MIGRATIONS_ROOT):
            open(os.path.join(settings.PG_VIEWS_MIGRATIONS_ROOT, '__index__.py'), 'a').close()

    def get_next_filename(self):
        last_filename = self.get_last_filename()
        return '{:0>4}.py'.format(int(last_filename[:4]) + 1) if last_filename else '0001.py'

    def write_dictionary(self, out, dictionary, prefix):
        for k, v in dictionary.items():
            if isinstance(v, dict):
                out.write('{prefix}\'{key}\': {{\n'.format(prefix=' ' * 4 * prefix, key=k))
                self.write_dictionary(out, v, prefix + 1)
                out.write('{prefix}}},\n'.format(prefix=' ' * 4 * prefix, key=k))
            else:
                out.write('{prefix}\'{key}\': \'{value}\',\n'.format(prefix=' ' * 4 * prefix, key=k, value=v))

    def write_descriptor(self, descriptor_diff, descriptor):
        self.init_view_migrations_root()
        with open(os.path.join(settings.PG_VIEWS_MIGRATIONS_ROOT, self.get_next_filename()), 'w') as f:
            f.write('# -*- coding: utf-8 -*-\n')
            f.write('from __future__ import unicode_literals\n\n\n')

            f.write('views_diff = {\n')
            self.write_dictionary(f, descriptor_diff, 1)
            f.write('}\n\n')

            f.write('views = {\n')
            self.write_dictionary(f, descriptor, 1)
            f.write('}\n')

    def generate_descriptor(self):
        descriptors = {}
        for model_view_class in get_sql_model_views():
            view = model_view_class()
            descriptor = {}
            descriptors[view.get_name()] = descriptor
            descriptor['verbose_name'] = view.model._meta.verbose_name
            fields_descriptor = {}
            descriptor['fields'] = fields_descriptor
            for name, (_, verbose_name, db_type) in model_view_class().get_columns().items():
                fields_descriptor[name] = {'verbose_name': verbose_name, 'db_type': db_type}
        return descriptors

    def get_descriptors_diff(self, prev_descriptors, new_descriptors):
        prev_descriptors = deepcopy(prev_descriptors)
        new_descriptors = deepcopy(new_descriptors)

        diff = {}
        for key in set(new_descriptors.keys()) - set(prev_descriptors.keys()):
            diff[key] = descriptor = new_descriptors.get(key)
            descriptor['alter_type'] = 'new'
        for key in set(prev_descriptors.keys()) - set(new_descriptors.keys()):
            diff[key] = descriptor = prev_descriptors.get(key)
            descriptor['alter_type'] = 'removed'
        for key in set(prev_descriptors.keys()) & set(new_descriptors.keys()):
            prev_descriptor = prev_descriptors.get(key)
            new_descriptor = new_descriptors.get(key)
            fields_diff = {}
            for name in set(new_descriptor['fields'].keys()) - set(prev_descriptor['fields'].keys()):
                field = new_descriptor['fields'].get(name)
                field['alter_type'] = 'new'
                fields_diff[name] = field
            for name in set(prev_descriptor['fields'].keys()) - set(new_descriptor['fields'].keys()):
                field = prev_descriptor['fields'].get(name)
                field['alter_type'] = 'removed'
                fields_diff[name] = field
            for name in set(prev_descriptor['fields'].keys()) & set(new_descriptor['fields'].keys()):
                prev_field = prev_descriptor['fields'].get(name)
                new_field = new_descriptor['fields'].get(name)
                if prev_field['db_type'] != new_field['db_type']:
                    new_field['alter_type'] = 'changed'
                    fields_diff[name] = new_field
            if fields_diff:
                new_descriptor['alter_type'] = 'changed'
                new_descriptor['fields'] = fields_diff
                diff[key] = new_descriptor
        return diff

    @translation_activate_block
    def handle(self, **options):
        last_descriptor = self.get_last_descriptor_views()
        descriptor = self.generate_descriptor()
        descriptors_diff = self.get_descriptors_diff(last_descriptor, descriptor)
        if not descriptors_diff:
            self.stdout.write('No view changes')
        else:
            self.write_descriptor(self.get_descriptors_diff(last_descriptor, descriptor), descriptor)
            self.stdout.write('Views migration was successfully generated')
