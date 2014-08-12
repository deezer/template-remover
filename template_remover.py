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

"""Replaces the template markup (PHP, Jinja, Mako) from an HTML file.

It replaces the markup so the lines and positions of actual HTML content is
preserved.

It uses Regexes to do the replacements so it is prone to errors in some corner
cases.
"""

from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
from __future__ import unicode_literals

from io import StringIO

import re


# Common patterns
LEADING_SPACES = r'(?P<spaces>^[\t ]+)'
NEW_LINE = r'(?P<newline>\n\r|\n|\r\n)'

# PHP patterns
PHP_START_ECHO = r'<\?='
PHP_START_TAG_WITH_ECHO = r'<\?php\s+echo'
PHP_START_TAG_SHORT_WITH_ECHO = r'<\?\s+echo'
PHP_START_TAG = r'<\?php'
# N.B.(skreft): there's no need to use a negative lookahead here [(?!=)], as the
# priority of start tags is lower than the one of echo tags.
PHP_START_TAG_SHORT = r'<\?'
PHP_END_TAG = r'\?>'

# Jinja patterns
JINJA_START_TAG = r'{%'
JINJA_START_ECHO = r'{{'
JINJA_END_TAG = r'%}'
JINJA_END_ECHO = r'}}'

# Mako patterns
MAKO_START_ECHO = r'\${'
MAKO_END_ECHO = r'}'
MAKO_START_TAG = (
    r'(</?%|%\s*(end)?(if|else|elif|for|while|try|catch|except|finally)|##)')
MAKO_END_TAG = r'([%/]?>|$)'


def get_pattern(echo_tags, start_tags, end_tags):
    """Constructs a pattern to use with the method clean().

    The priority of the tags is echo_tags, then start_tags and finally end_tags.
    That means that in some cases a negative lookahead may be required, as the
    first match from left to right will be reported.

    See clean() for the meaning of each group.

    Args:
      echo_tags: list of re strings. These are tags that may output something.
      start_tags: list of re strings. Tags that typically do not output
        anything, like control structures.
      end_tags: list of re strings. All the closing tags.

    Returns:
      a RegexObject.
    """
    return re.compile(
        '|'.join((
            LEADING_SPACES,
            NEW_LINE,
            r'(?P<echo>%s)' % '|'.join(echo_tags),
            r'(?P<start>%s)' % '|'.join(start_tags),
            r'(?P<end>%s)' % '|'.join(end_tags))),
        flags=re.MULTILINE)


JINJA_PATTERN = get_pattern(
    [JINJA_START_ECHO],
    [JINJA_START_TAG],
    [JINJA_END_TAG, JINJA_END_ECHO])

PHP_PATTERN = get_pattern(
    [PHP_START_ECHO, PHP_START_TAG_WITH_ECHO, PHP_START_TAG_SHORT_WITH_ECHO],
    [PHP_START_TAG, PHP_START_TAG_SHORT],
    [PHP_END_TAG])

MAKO_PATTERN = get_pattern(
    [MAKO_START_ECHO],
    [MAKO_START_TAG],
    [MAKO_END_TAG, MAKO_END_ECHO])

ALL_PATTERN = get_pattern(
    [PHP_START_ECHO, PHP_START_TAG_WITH_ECHO, PHP_START_TAG_SHORT_WITH_ECHO,
        JINJA_START_ECHO, MAKO_START_ECHO],
    [PHP_START_TAG, PHP_START_TAG_SHORT, JINJA_START_TAG, MAKO_START_TAG],
    [PHP_END_TAG, JINJA_END_TAG, JINJA_END_ECHO, MAKO_END_TAG, MAKO_END_ECHO])


def _get_tag(match):
    groups = match.groupdict()
    if groups.get('echo') is not None:
        return 'ECHO'
    elif groups.get('end') is not None:
        return 'END'
    elif groups.get('start') is not None:
        return 'START'
    elif groups.get('newline') is not None:
        return 'NEWLINE'
    elif groups.get('spaces') is not None:
        return 'SPACES'

    print(groups)
    assert False, ('Only the groups "echo", "end", "start", "newline" and ' +
                   '"spaces" are allowed. Please correct your pattern or use ' +
                   'the method get_pattern() to construct it.')


class _TemplateRemover(object):
    """Helper class for the clean() method.

    This class exists mainly to factor out some methods.
    """
    def __init__(self, html_content, pattern=ALL_PATTERN):
        self.html_content = html_content
        self.pattern = pattern
        self._output = StringIO()
        self._index = 0
        self._state = 'HTML'
        self._pending = []
        self._pending_has_blank = False

    def _reset_pending(self):
        self._pending = []
        self._pending_has_blank = False

    def _write_content(self, end=None):
        self._output.writelines(self._pending)
        self._reset_pending()
        self._output.write(self.html_content[self._index:end])

    def get_clean_content(self):
        """Implementation of the clean() method."""
        fill_chars = {'BLANK_TEMPLATE': ' ', 'ECHO_TEMPLATE': '0'}
        for match in self.pattern.finditer(self.html_content):
            start, end = match.start(), match.end()
            tag = _get_tag(match)
            if tag == 'ECHO':
                self._write_content(start)
                self._index = start
                self._state = 'ECHO_TEMPLATE'
            elif tag == 'START':
                if self._index != start:
                    self._write_content(start)
                self._index = start
                self._state = 'BLANK_TEMPLATE'
            elif tag == 'END':
                if self._state not in ('BLANK_TEMPLATE', 'ECHO_TEMPLATE'):
                    # We got a closing tag but none was open. We decide to carry
                    # on as it may be the case that it was because of a closing
                    # dictionary in javascript like: var dict = {foo:{}}.
                    # See the note on the clean() function for more details.
                    continue
                fill_char = fill_chars[self._state]
                fill = fill_char * (end - self._index)
                if self._state == 'BLANK_TEMPLATE':
                    self._pending.append(fill)
                    self._pending_has_blank = True
                else:
                    assert not self._pending
                    self._output.write(fill)
                self._index = end
                self._state = 'HTML'
            elif tag == 'SPACES':
                self._pending.append(match.group('spaces'))
                self._index = end
            elif tag == 'NEWLINE':
                if self._state == 'HTML':
                    if self._index != start or not self._pending_has_blank:
                        self._write_content(start)
                    self._output.write(match.group('newline'))
                elif self._state == 'BLANK_TEMPLATE':
                    # We discard the content of this template and whatever is in
                    # self._pending.
                    self._output.write(match.group('newline'))
                elif self._state == 'ECHO_TEMPLATE':
                    assert False, 'Echo tags should be in just one line.'
                self._index = end
                self._reset_pending()

        assert self._state == 'HTML', 'Tag was not closed'
        if self._index != len(self.html_content) or not self._pending_has_blank:
            self._write_content()

        return self._output.getvalue()


def clean(html_content, pattern=ALL_PATTERN):
    """Removes the markup from the supplied string.

    Note: this is not a fully compliant markup remover as it is only based in
    some regular expressions. This means there are some edge cases that cannot
    be captured with this method. Although we believe those cases are too
    contrived, and probably should be avoided as some development tools will
    fail as well.

    One example that won't work is the following:
        <?php echo "?>" ?>
    The reason it does not work is because when the method sees the first '?>'
    (the one inside the string), it thinks it's a closing tag.

    This method works by finding the beginning and ending of the tags. The tags
    are grouped in three categories.
      echo_tags: these are tags that will typically produce some output and
        should be replaced with actual content not blanks. It will output as
        many zeroes as the length of the original tag. The length is preserved
        so the columns and lines are preserved for the html. The filling
        character is a '0', just because is a valid value for a number and some
        html attributes require numbers.
        Strong assumption: this tag should be in just one line.
        For example, href="<?= $foo ?>" is replaced with href="00000000000".
      start_tags: these tags do not usually print content, these are mainly
        control structures. The content of this tag is replaced by blanks or
        removed depending on the context. If the tag is open and closed in the
        same line then it is replaced by the same number of blanks, but only if
        there was nonblank content before or after. If there is multiline then
        the contents are just removed. The contents are stripped, so there are
        no trailing spaces introduced by the markup.
        For example:
        "  <?php if { ?>" is replaced by ""
        but
        "  <?php if { ?>  <!-- A comment ->" is replaced by
        "                 <!-- A comment ->"
      end_tags: the closing tags for both echo and start tags. They trigger the
      output.

    Args:
      html_content: the string to be cleaned.
      pattern: a RegexObject containing only the groups "echo", "end", "start",
        "newline" and "spaces". Use the method get_pattern to construct it.
        By default it will clean all defined markups (PHP and Jinja).

    Returns:
      A string with the markup removed.
    """
    return _TemplateRemover(html_content, pattern).get_clean_content()


def clean_php(html_content):
    """Removes the PHP markup from the supplied string.

    It does not support the optional asp tags.

    See clean() for more details.
    """
    return clean(html_content, pattern=PHP_PATTERN)


def clean_jinja(html_content):
    """Removes the Jinja markup from the supplied string.

    See clean() for more details.
    """
    return clean(html_content, pattern=JINJA_PATTERN)


def clean_mako(html_content):
    """Removes the Mako markup from the supplied string.

    See clean() for more details.
    """
    return clean(html_content, pattern=MAKO_PATTERN)
