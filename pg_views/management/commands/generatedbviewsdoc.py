import os

from django.conf import settings
from django.core.management.base import BaseCommand, CommandError
from django.utils.translation import ugettext

from chamber.utils.decorators import translation_activate_block

from pg_views.management.commands import CommandMixin


class Command(CommandMixin, BaseCommand):

    help = 'Generate views documentation.'

    def init_view_doc_root(self):
        if not os.path.exists(settings.PG_VIEWS_MIGRATIONS_DOC_ROOT):
            os.makedirs(settings.PG_VIEWS_MIGRATIONS_DOC_ROOT)

    def generate_doc_file(self, current_views, diff_views):
        change_types = {
            'new': ugettext('New'),
            'changed': ugettext('Changed'),
            'removed': ugettext('Removed'),
        }

        self.init_view_doc_root()
        try:
            import xlsxwriter
        except ImportError:
            raise CommandError('xlswriter library must be installed')

        workbook = xlsxwriter.Workbook(os.path.join(settings.PG_VIEWS_MIGRATIONS_DOC_ROOT, 'views_documentation.xlsx'))

        for label, views, has_alter in ((ugettext('Diff'), diff_views, True), (ugettext('All'), current_views, False)):
            worksheet = workbook.add_worksheet(label)
            worksheet.set_column(0, 0, 32)
            worksheet.set_column(1, 1, 20)
            worksheet.set_column(2, 2, 50)
            worksheet.set_column(3, 3, 15)

            header_format = workbook.add_format({'bold': True})
            removed_format = workbook.add_format({'font_color': 'red'})
            created_format = workbook.add_format({'font_color': 'green'})

            row = 0
            for view_name in sorted(views.keys()):
                view = views.get(view_name)
                label, alter_type = view.get('verbose_name'), view.get('alter_type')

                format = created_format if alter_type == 'new' else (removed_format if alter_type == 'removed' else None)

                worksheet.write(row, 0, ugettext('Name'), header_format)
                worksheet.write(row, 1, ugettext('Label'), header_format)
                if has_alter:
                    worksheet.write(row, 2, ugettext('Alter'), header_format)
                row += 1
                worksheet.write(row, 0, view_name, format)
                worksheet.write(row, 1, label, format)
                if has_alter:
                    worksheet.write(row, 2, change_types.get(alter_type), format)
                row += 1
                worksheet.write(row, 0, ugettext('Field name'), header_format)
                worksheet.write(row, 1, ugettext('Column type'), header_format)
                worksheet.write(row, 2, ugettext('Field label'), header_format)
                if alter_type:
                    worksheet.write(row, 3, ugettext('Field alter'), header_format)
                row += 1
                for field_name in sorted(view.get('fields').keys()):
                    field = view.get('fields').get(field_name)
                    field_label, field_alter_type, field_db_type = (
                        field.get('verbose_name'), field.get('alter_type'), field.get('db_type')
                    )
                    field_format = (
                        created_format if field_alter_type == 'new'
                        else (removed_format if field_alter_type == 'removed' else format)
                    )
                    worksheet.write(row, 0, field_name, field_format)
                    worksheet.write(row, 1, field_db_type, field_format)
                    worksheet.write(row, 2, field_label, field_format)
                    if has_alter:
                        worksheet.write(row, 3, change_types.get(field_alter_type), field_format)
                    row += 1
                row += 2

    @translation_activate_block
    def handle(self, **options):
        if not self.get_last_filename():
            self.stderr.write('Migration file was not found')
        else:
            self.generate_doc_file(self.get_last_descriptor_views(), self.get_last_descriptor_views_diff())
            self.stdout.write('Doc was generated {}'.format(
                os.path.join(settings.PG_VIEWS_MIGRATIONS_DOC_ROOT, 'views_documentation.xlsx')
            ))
