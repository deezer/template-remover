Template Remover
================

.. image:: https://badge.fury.io/py/template-remover.png
    :target: http://badge.fury.io/py/template-remover

.. image:: https://travis-ci.org/deezer/template-remover.png?branch=master
    :target: https://travis-ci.org/deezer/template-remover

.. image:: https://coveralls.io/repos/deezer/template-remover/badge.png?branch=master
    :target: https://coveralls.io/r/deezer/template-remover?branch=master


Template remover is a tool to remove the PHP and Jinja markup from HTML files.

Motivation
----------

Many tools, like html tidy, are designed to parse and analyze html files,
however they do not play well when there is language markup. This projects aims
to be a simple way of getting rid of those markups.

Limitations
-----------

template_remover is based on regular expressions. This means that there are some
edge cases that cannot be captured with this method. Although we believe those
cases are too contrived, and probably should be avoided as many development
tools will fail as well.

One example that won't work is the following:::

  <?php echo "?>" ?>

The reason it does not work is because when the method sees the first '?>'
(the one inside the string), it thinks it's a closing tag.


Example use
-----------

Below are example of how template_remover.py is used::

  $ remove_template.py filename.html
  $ remove_template.py filename.html | tidy -qe


Installation
------------

You can install, upgrade or uninstall git-lint with these commands::

  $ pip install template-remover
  $ pip install --upgrade template-remover
  $ pip uninstall template-remover

Python Versions
---------------

Python 2.7, 3.2 and 3.3 are supported.

Development
-----------

Help for this project is more than welcomed, so feel free to create an issue or
to send a pull request via http://github.com/deezer/template-remover.

Tests are run using nose, either with::

  $ python -R setup.py nosetests
  $ nosetests

Use the tool `git-lint <https://github.com/sk-/git-lint>`_ before any commit, so
errors and style problems are caught early.

TODOS and Possible Features
---------------------------

* Support more template engines and languages (Smarty, ASP, JSP, etc).


Changelog
=========

v0.1 (2014-05-07)
-------------------

* Initial commit.