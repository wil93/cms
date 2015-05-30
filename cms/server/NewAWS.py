#!/usr/bin/env python2
# -*- coding: utf-8 -*-

# Contest Management System - http://cms-dev.github.io/
# Copyright © 2015 William Di Luigi <williamdiluigi@gmail.com>
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

"""Web server for administration of contests.

"""

from __future__ import absolute_import
from __future__ import print_function
from __future__ import unicode_literals

import base64
import json
import logging
import os
import pkg_resources
import re
import traceback
from datetime import datetime, timedelta
from StringIO import StringIO
import zipfile

from sqlalchemy.orm import joinedload
from sqlalchemy.exc import IntegrityError

import tornado.web
import tornado.locale

from cms import config, ServiceCoord, get_service_shards, get_service_address
from cms.io import WebService
from cms.db import Session, Contest, User, Announcement, Question, Message, \
    Submission, File, Task, Dataset, Attachment, Manager, Testcase, \
    SubmissionFormatElement, Statement, Participation, Base
from cms.db.filecacher import FileCacher
from cms.grading import compute_changes_for_dataset
from cms.grading.tasktypes import get_task_type_class
from cms.grading.scoretypes import get_score_type_class
from cms.server import file_handler_gen, get_url_root, \
    CommonRequestHandler
from cmscommon.datetime import make_datetime, make_timestamp


logger = logging.getLogger(__name__)


from datetime import timedelta

from eve import Eve
from eve_sqlalchemy import SQL
from eve_sqlalchemy.decorators import registerSchema
from eve.io.base import BaseJSONEncoder

registerSchema('contest')(Contest)
registerSchema('question')(Question)

SETTINGS = {
    'DEBUG': True,
    'SQLALCHEMY_DATABASE_URI': config.database,
    'DOMAIN': {
        'contest': Contest._eve_schema['contest'],
        'question': Question._eve_schema['question'],
    }
}

class SQLAJSONEncoder(BaseJSONEncoder):
    def default(self, obj):
        if isinstance(obj, timedelta):
            return obj.total_seconds()
        return super(SQLAJSONEncoder, self).default(obj)


class CustomData(SQL):
    json_encoder_class = SQLAJSONEncoder


app = Eve(data=CustomData, settings=SETTINGS)

db = app.data.driver
Base.metadata.bind = db.engine
db.Model = Base


def main():
    app.run()
