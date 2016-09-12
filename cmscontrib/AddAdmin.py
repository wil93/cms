#!/usr/bin/env python2
# -*- coding: utf-8 -*-

# Contest Management System - http://cms-dev.github.io/
# Copyright © 2015 Stefano Maggiolo <s.maggiolo@gmail.com>
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

"""This script creates a new admin in the database.

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

from cms import utf8_decoder
from cms.db import Admin, SessionGen
from cmscommon.crypto import generate_random_password, hash_password

from sqlalchemy.exc import IntegrityError


logger = logging.getLogger(__name__)


def add_admin(username, password=None):
    logger.info("Creating the admin on the database.")
    
    if password is None:
        password = generate_random_password()

    admin = Admin()

    admin.username = username
    admin.authentication = hash_password(password.encode("utf-8"))
    admin.name = username
    admin.permission_all = True

    try:
        with SessionGen() as session:
            session.add(admin)
            session.commit()
    except IntegrityError:
        logger.exception("An admin with the given username already exists.")
        return False

    logger.info("Admin with complete access added. "
                "Login with username %s and password %s",
                username, password)
    return True


def main():
    """Parse arguments and launch process.

    """
    parser = argparse.ArgumentParser(description="Add an admin to CMS.")
    parser.add_argument("username", action="store", type=utf8_decoder,
                        nargs=1)
    parser.add_argument("-p", "--password", action="store", type=utf8_decoder)

    args = parser.parse_args()

    return add_admin(args.username[0], args.password)


if __name__ == "__main__":
    sys.exit(0 if main() is True else 1)
