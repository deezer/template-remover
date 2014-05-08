#!/usr/bin/env python
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

"""remove_template.py

Removes the PHP or Jinja2 markup from html files.

This software is released under the Apache License. Copyright Deezer 2014.

Usage:
  remove_template.py FILENAME
  remove_template.py (-h | --help)
  remove_template.py --version

Options:
  -h --help        Show this screen.
  --version        Show version.
"""

from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
from __future__ import unicode_literals

import codecs
import io
import sys

import docopt

import template_remover


__VERSION__ = '0.1'


def main():
    """Entry point for remove_template."""

    # Wrap sys stdout for python 2, so print can understand unicode.
    if sys.version_info[0] < 3:
        sys.stdout = codecs.getwriter("utf-8")(sys.stdout)

    options = docopt.docopt(__doc__,
                            help=True,
                            version='template_remover v%s' % __VERSION__)

    print(template_remover.clean(io.open(options['FILENAME']).read()))

    return 0

if __name__ == '__main__':
    sys.exit(main())
