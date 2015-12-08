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

"""Web server for administration of contests, tasks, users, and so on.

"""

from flask import Flask
from flask_admin import Admin
from flask_sqlalchemy import SQLAlchemy

from flask_admin.contrib.sqla import ModelView

from cms import config
from cms.db import Contest, Participation, Task, Team, User


def main():
    app = Flask(__name__)
    app.config['SQLALCHEMY_DATABASE_URI'] = config.database
    db = SQLAlchemy(app)

    admin = Admin(app, name='admin-web-server', template_mode='bootstrap3')
    admin.add_view(ModelView(Contest, db.session))
    admin.add_view(ModelView(Participation, db.session))
    admin.add_view(ModelView(Task, db.session))
    admin.add_view(ModelView(Team, db.session))
    admin.add_view(ModelView(User, db.session))

    app.run()
