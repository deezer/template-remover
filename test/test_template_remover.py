# Copyright 2014 Deezer (http://www.deezer.com)
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

"""Tests for the template_remover module."""

from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
from __future__ import unicode_literals

import re
import unittest

import template_remover

# pylint: disable=too-many-public-methods


class TestTemplateRemover(unittest.TestCase):
    def test_clean_invalid_pattern(self):
        with self.assertRaises(AssertionError):
            template_remover.clean('foo', re.compile(r'\w'))

    def test_clean_php_open_tag_at_eof(self):
        with self.assertRaises(AssertionError):
            template_remover.clean_php('<?php')

    def test_clean_php_inline_echo(self):
        self.assertEquals(
            '<a href="00000000000">Link</a>',
            template_remover.clean_php('<a href="<?= $foo ?>">Link</a>')
        )

    def test_clean_php_inline_echho_not_closed(self):
        with self.assertRaises(AssertionError):
            template_remover.clean_php('<a href="<?= $foo \n')

    def test_clean_php_echo(self):
        self.assertEquals(
            '<a href="0000000000000000000">Link</a>',
            template_remover.clean_php('<a href="<?php echo $foo; ?>">Link</a>')
        )

    def test_clean_php_short_echo(self):
        self.assertEquals(
            '<a href="0000000000000000">Link</a>',
            template_remover.clean_php('<a href="<? echo $foo; ?>">Link</a>')
        )

    def test_clean_php_inline_echo_mixed(self):
        self.assertEquals(
            '         <a href="00000000000">Link</a>',
            template_remover.clean_php(
                ' <?php ?><a href="<?= $foo ?>">Link</a>')
        )

    def test_clean_php_control(self):
        self.assertEquals(
            '                      <a href="#next">Next</a>',
            template_remover.clean_php(
                '<?php if ($a > 1) { ?><a href="#next">Next</a><?php } ?>')
        )

    def test_clean_php_short_tags(self):
        self.assertEquals(
            'a       b',
            template_remover.clean_php('a <? ?> b')
        )

    def test_clean_php_control_multiline(self):
        self.assertEquals(
            '\n\n',
            template_remover.clean_php(
                '  <?php if ($a > 1) {    \n echo "foo"\n  } ?>')
        )

    def test_clean_php_multiline(self):
        self.assertEquals(
            '                      <a href="#next">Next</a>\n' +
            '<a href="00000000000">Link</a>',
            template_remover.clean_php(
                '<?php if ($a > 1) { ?><a href="#next">Next</a><?php } ?>\n' +
                '<a href="<?= $foo ?>">Link</a>')
        )

    def test_spaces_are_preserved(self):
        self.assertEquals(
            '  \t\n    ',
            template_remover.clean_php('  \t\n    ')
        )

    def test_php_control_at_end(self):
        self.assertEquals(
            '            placeholder  ',
            template_remover.clean_php('  <?php ?>  placeholder  ')
        )

    def test_unicode(self):
        self.assertEquals(
            'ni\xf1o',
            template_remover.clean_php('ni\xf1o')
        )
        self.assertEquals(
            '\xe9',
            template_remover.clean_php('\xe9')
        )

    def test_php_comprehensive(self):
        template = '''<html>
          <body>
          
          <?php if($foo) { ?>
            <a href="<?= $foo ?>"><a>
          <?php } ?>  <!-- comment ->

          
        '''
        expected = '''<html>
          <body>
          

            <a href="00000000000"><a>
                      <!-- comment ->

          
        '''
        self.assertEquals(expected, template_remover.clean_php(template))

    def test_jinja_comprehensive(self):
        template = '''<html>
          <body>
          
          {% if foo %}
            <a href="{{foo}}"><a>
          {% endif %}  <!-- comment ->

          
        '''
        expected = '''<html>
          <body>
          

            <a href="0000000"><a>
                       <!-- comment ->

          
        '''
        self.assertEquals(expected, template_remover.clean_jinja(template))

    def test_jinja_does_not_complain_with_double_braces(self):
        template = '<script>var dict={foo:{}}</script>'
        expected = '<script>var dict={foo:{}}</script>'
        self.assertEquals(expected, template_remover.clean_jinja(template))

    def test_mako_comprehensive(self):
        template = '''<html>
          <body>
          
          <a title="${"this is some text" | u}">Foo</a>
          % if x == 5:
            <a href="${foo}"><a>
          % endif
          <%
            x = db.get_resource('foo')
            y = [z.element for z in x if x.frobnizzle==5]
          %>
          <%include file="foo.txt"/>
          ## Comment
          <%def name="foo" buffered="True">
            this is a def
          </%def>
          
        '''
        expected = '''<html>
          <body>
          
          <a title="00000000000000000000000000">Foo</a>

            <a href="000000"><a>








            this is a def

          
        '''
        self.assertEquals(expected, template_remover.clean_mako(template))
