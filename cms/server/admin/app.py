#!/usr/bin/env python2
# -*- coding: utf-8 -*-

# Contest Management System - http://cms-dev.github.io/
# Copyright © 2015-2016 William Di Luigi <williamdiluigi@gmail.com>
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
from flask_admin.contrib.sqla import ModelView
from flask_admin.form.upload import FileUploadField
from flask_admin.consts import ICON_TYPE_FONT_AWESOME

from flask_sqlalchemy import SQLAlchemy

from jinja2 import Markup

from cms.db import Contest, Participation, Task, Team, User


class ListUsersView(ModelView):
    column_select_related_list = ('user', 'city')

class UserAdminView(ModelView):
    def picture_validation(self, field):
        __import__("pdb").set_trace()
        if field.data:
            filename = field.data.filename
            if filename[-4:] != '.jpg':
                raise Exception('file must be .jpg')
            if False:  #imghdr.what(field.data) != 'jpeg':
                raise Exception('file must be a valid jpeg image.')
            field.data = field.data.stream.read()
            return True
        else:
            return False

    column_searchable_list = ('username', 'first_name', 'last_name', 'email')
    #column_labels = dict(id='ID', first_name="First name", face='Picture')
    column_descriptions = dict(
        username='This username will be required to login',
        password='The default password (caution: stored in plain text!)',
        face='The profile picture (that will be seen in the ranking)',
        timezone='Timezone of the contestant, used to display start, end '
                 'times and the current server time in local time. Example: '
                 '\'Europe/Rome\', \'America/New_York\', ...',
        preferred_languages='JSON-encoded list of language codes, from the '
                            'most to the least preferred. Example: \'["en", '
                            '"ja"]\'',
    )

    def pic_formatter(self, context, model, name):
        if getattr(model, name):
            return Markup('<span style="color: green">picture</span>')
        else:
            return Markup('<span style="color: red">NULL</span>')

    column_formatters = dict(face=pic_formatter)
    form_overrides = dict(face=FileUploadField)
    form_args = dict(face=dict(validators=[picture_validation]))


def main():
    app = Flask(__name__)
    app.config.from_pyfile('config.py')
    db = SQLAlchemy(app)

    admin = Admin(app, name='Admin', template_mode='bootstrap3', base_template='admin/new_base.html')
    admin.add_view(ModelView(Contest, db.session, menu_icon_type=ICON_TYPE_FONT_AWESOME, menu_icon_value='fa-trophy fa-lg'))
    admin.add_view(ModelView(Task, db.session, menu_icon_type=ICON_TYPE_FONT_AWESOME, menu_icon_value='fa-list fa-lg'))
    admin.add_view(UserAdminView(User, db.session, menu_icon_type=ICON_TYPE_FONT_AWESOME, menu_icon_value='fa-user fa-lg'))
    #admin.add_view(ModelView(Participation, db.session, ))
    admin.add_view(ModelView(Team, db.session, menu_icon_type=ICON_TYPE_FONT_AWESOME,
        menu_icon_value='fa-users fa-lg'))

    @app.route('/')
    def index():
        return '<a href="/admin/">Click me to get to Admin!</a>'

    app.run(debug=True)

if __name__ == "__main__":
    main()
