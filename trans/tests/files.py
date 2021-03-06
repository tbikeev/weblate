# -*- coding: utf-8 -*-
#
# Copyright © 2012 - 2013 Michal Čihař <michal@cihar.com>
#
# This file is part of Weblate <http://weblate.org/>
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.
#

"""
Tests for import and export.
"""

from trans.tests.views import ViewTestCase
from django.core.urlresolvers import reverse
from trans.tests.util import get_test_file

TEST_PO = get_test_file('cs.po')

TRANSLATION_OURS = u'Nazdar světe!\n'
TRANSLATION_PO = u'Ahoj světe!\n'


class ImportTest(ViewTestCase):
    '''
    Testing of file imports.
    '''

    def setUp(self):
        super(ImportTest, self).setUp()
        # We need extra privileges for overwriting
        self.user.is_superuser = True
        self.user.save()

    def do_import(self, **kwargs):
        '''
        Helper to perform file import.
        '''
        with open(TEST_PO) as handle:
            params = {'file': handle}
            params.update(kwargs)
            return self.client.post(
                reverse(
                    'upload_translation',
                    kwargs=self.kw_translation
                ),
                params
            )

    def test_import_normal(self):
        '''
        Test importing normally.
        '''
        response = self.do_import()
        self.assertRedirects(response, self.translation_url)

        # Verify stats
        translation = self.get_translation()
        self.assertEquals(translation.translated, 1)
        self.assertEquals(translation.fuzzy, 0)
        self.assertEquals(translation.total, 4)

        # Verify unit
        unit = self.get_unit()
        self.assertEquals(unit.target, TRANSLATION_PO)

    def test_import_author(self):
        '''
        Test importing normally.
        '''
        response = self.do_import(
            author_name='Testing User',
            author_email='noreply@weblate.org'
        )
        self.assertRedirects(response, self.translation_url)

        # Verify stats
        translation = self.get_translation()
        self.assertEquals(translation.translated, 1)
        self.assertEquals(translation.fuzzy, 0)
        self.assertEquals(translation.total, 4)

        # Verify unit
        unit = self.get_unit()
        self.assertEquals(unit.target, TRANSLATION_PO)

    def test_import_overwrite(self):
        '''
        Test importing with overwriting.
        '''
        # Translate one unit
        self.change_unit(TRANSLATION_OURS)

        response = self.do_import(overwrite='yes')
        self.assertRedirects(response, self.translation_url)

        # Verify unit
        unit = self.get_unit()
        self.assertEquals(unit.target, TRANSLATION_PO)

    def test_import_no_overwrite(self):
        '''
        Test importing without overwriting.
        '''
        # Translate one unit
        self.change_unit(TRANSLATION_OURS)

        response = self.do_import()
        self.assertRedirects(response, self.translation_url)

        # Verify unit
        unit = self.get_unit()
        self.assertEquals(unit.target, TRANSLATION_OURS)

    def test_import_fuzzy(self):
        '''
        Test importing as fuzzy.
        '''
        response = self.do_import(method='fuzzy')
        self.assertRedirects(response, self.translation_url)

        # Verify unit
        unit = self.get_unit()
        self.assertEquals(unit.target, TRANSLATION_PO)
        self.assertEquals(unit.fuzzy, True)

        # Verify stats
        translation = self.get_translation()
        self.assertEquals(translation.translated, 0)
        self.assertEquals(translation.fuzzy, 1)
        self.assertEquals(translation.total, 4)

    def test_import_suggest(self):
        '''
        Test importing as suggestion.
        '''
        response = self.do_import(method='suggest')
        self.assertRedirects(response, self.translation_url)

        # Verify unit
        unit = self.get_unit()
        self.assertEquals(unit.translated, False)

        # Verify stats
        translation = self.get_translation()
        self.assertEquals(translation.translated, 0)
        self.assertEquals(translation.fuzzy, 0)
        self.assertEquals(translation.total, 4)
        self.assertEquals(
            translation.have_suggestion,
            1
        )


class ExportTest(ViewTestCase):
    '''
    Testing of file export.
    '''
    def create_subproject(self):
        # Needs to create PO file to have language pack option
        return self.create_po()

    def test_export(self):
        response = self.client.get(
            reverse(
                'download_translation',
                kwargs=self.kw_translation
            )
        )
        self.assertContains(response, 'Weblate Hello World 2012')
        self.assertEqual(
            response['Content-Disposition'],
            'attachment; filename=test-test-cs.po'
        )

    def test_language_pack(self):
        response = self.client.get(
            reverse(
                'download_language_pack',
                kwargs=self.kw_translation
            )
        )
        self.assertEqual(
            response['Content-Disposition'],
            'attachment; filename=cs.mo'
        )
