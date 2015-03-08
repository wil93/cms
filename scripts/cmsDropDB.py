# -*- coding: utf-8 -*-

# Contest Management System - http://cms-dev.github.io/
# Copyright © 2013-2014 Luca Wehrstedt <luca.wehrstedt@gmail.com>
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU Affero General Public License as
# published by the Free Software Foundation, either version 3 of the
# License, or (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU Affero General Public License for more details.
#
# You should have received a copy of the GNU Affero General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.

"""Script to drop the database data and schema used by CMS.

It will work with a database initialized and populated by any version
of CMS as it uses (PostgreSQL-specific) SQL queries to drop the whole
database. This also means that other data in the same database used
by CMS will be deleted as well.

"""

from __future__ import absolute_import
from __future__ import print_function
from __future__ import unicode_literals

# We enable monkey patching to make many libraries gevent-friendly
# (for instance, urllib3, used by requests)
import gevent.monkey
gevent.monkey.patch_all()

import argparse
import logging
import sys

from cms import ConfigError
from cms.db import test_db_connection, drop_db


logger = logging.getLogger(__name__)


def main():
    """Parse arguments and perform operation.

    """
    test_db_connection()

    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("-y", "--yes", action="store_true",
                        help="do not require confirmation")
    args = parser.parse_args()

    if not args.yes:
        print("Are you sure you want to DROP the database? [y/N] ", end='')
        ans = sys.stdin.readline().strip().lower()
        if ans in ["y", "yes"]:
            args.yes = True

    if args.yes:
        print("Dropping database.")
        return drop_db()
    else:
        print("Not dropping database.")
        return True


def cli():
    try:
        sys.exit(0 if main() is True else 1)
    except ConfigError as error:
        logger.critical(error.message)
        sys.exit(1)
