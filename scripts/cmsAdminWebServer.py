# -*- coding: utf-8 -*-

# Contest Management System - http://cms-dev.github.io/
# Copyright © 2013 Luca Wehrstedt <luca.wehrstedt@gmail.com>
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

from __future__ import absolute_import
from __future__ import print_function
from __future__ import unicode_literals

# We enable monkey patching to make many libraries gevent-friendly
# (for instance, urllib3, used by requests)
import gevent.monkey
gevent.monkey.patch_all()

import logging
import sys

from cms import ConfigError, default_argument_parser
from cms.db import test_db_connection
from cms.server.AdminWebServer import AdminWebServer


logger = logging.getLogger(__name__)


def main():
    """Parse arguments and launch service.

    """
    test_db_connection()
    return default_argument_parser("Admins' web server for CMS.",
                                   AdminWebServer).run()


def cli():
    try:
        sys.exit(0 if main() is True else 1)
    except ConfigError as error:
        logger.critical(error.message)
        sys.exit(1)
