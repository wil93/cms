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

import argparse
import logging
import sys

from cms import ConfigError, get_safe_shard
from cms.db import ask_for_contest, is_contest_id, test_db_connection
from cms.service.ResourceService import ResourceService


logger = logging.getLogger(__name__)


def main():
    """Parses arguments and launch service.

    """
    parser = argparse.ArgumentParser(
        description="Resource monitor and service starter for CMS.")
    parser.add_argument("-a", "--autorestart", action="store", type=int,
                        nargs="?", const=-1, metavar="CONTEST_ID",
                        help="restart automatically services on its machine")
    parser.add_argument("shard", action="store", type=int, nargs="?")
    args = parser.parse_args()

    try:
        args.shard = get_safe_shard("ResourceService", args.shard)
    except ValueError:
        return False

    test_db_connection()

    if args.autorestart is not None:
        if args.autorestart == -1:
            ResourceService(args.shard,
                            contest_id=ask_for_contest()).run()
        else:
            if is_contest_id(args.autorestart):
                ResourceService(args.shard, contest_id=args.autorestart).run()
            else:
                print("There is no contest with the specified id. "
                      "Please try again.", file=sys.stderr)
                return False
    else:
        return ResourceService(args.shard).run()


def cli():
    try:
        sys.exit(0 if main() is True else 1)
    except ConfigError as error:
        logger.critical(error.message)
        sys.exit(1)
