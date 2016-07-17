import os

import re

from django.conf import settings

from import_file import import_file


class CommandMixin(object):

    migration_file_regex = re.compile(r'^\d{4}\.py$')

    def get_last_filename(self):
        filenames = (
            sorted(filter(lambda filename: self.migration_file_regex.match(filename),
                          os.listdir(settings.PG_VIEWS_MIGRATIONS_ROOT)))
            if os.path.exists(settings.PG_VIEWS_MIGRATIONS_ROOT) else ()
        )
        return filenames[-1] if filenames else None

    def get_last_descriptor_views(self):
        last_filename = self.get_last_filename()
        return (
            import_file(os.path.join(settings.PG_VIEWS_MIGRATIONS_ROOT, last_filename)).views if last_filename else {}
        )

    def get_last_descriptor_views_diff(self):
        last_filename = self.get_last_filename()
        return (
            import_file(os.path.join(settings.PG_VIEWS_MIGRATIONS_ROOT, last_filename)).views_diff
            if last_filename else {}
        )
