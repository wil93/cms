#!/usr/bin/env python2
# -*- coding: utf-8 -*-

# Contest Management System - http://cms-dev.github.io/
# Copyright © 2010-2013 Giovanni Mascellani <mascellani@poisson.phc.unipi.it>
# Copyright © 2010-2015 Stefano Maggiolo <s.maggiolo@gmail.com>
# Copyright © 2010-2012 Matteo Boscariol <boscarim@hotmail.com>
# Copyright © 2012-2014 Luca Wehrstedt <luca.wehrstedt@gmail.com>
# Copyright © 2014 Artem Iglikov <artem.iglikov@gmail.com>
# Copyright © 2014 Fabian Gundlach <320pointsguy@gmail.com>
# Copyright © 2016 Myungwoo Chun <mc.tamaki@gmail.com>
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

"""User-related handlers for AWS.

"""

from __future__ import absolute_import
from __future__ import print_function
from __future__ import unicode_literals

from cms.db import Contest, Participation, User, Team
from cmscommon.datetime import make_datetime

from .base import BaseHandler, SimpleHandler, require_permission


class UserHandler(BaseHandler):
    @require_permission(BaseHandler.PERMISSION_ALL)
    def get(self, user_id):
        user = self.safe_get_item(User, user_id)

        self.r_params = self.render_params()
        self.r_params["user"] = user
        self.r_params["participations"] = \
            self.sql_session.query(Participation)\
                .filter(Participation.user == user)\
                .all()
        self.r_params["unassigned_contests"] = \
            self.sql_session.query(Contest)\
                .filter(not Contest.id.in_(
                    self.sql_session.query(Participation.contest_id)
                        .filter(Participation.user is user)
                        .all()))\
                .all()
        self.render("user.html", **self.r_params)

    @require_permission(BaseHandler.PERMISSION_ALL)
    def post(self, user_id):
        fallback_page = "/user/%s" % user_id

        user = self.safe_get_item(User, user_id)

        try:
            attrs = user.get_attrs()

            self.get_string(attrs, "first_name")
            self.get_string(attrs, "last_name")
            self.get_string(attrs, "username", empty=None)
            self.get_string(attrs, "password")
            self.get_string(attrs, "email")
            self.get_string(attrs, "preferred_languages")
            self.get_string(attrs, "timezone", empty=None)

            assert attrs.get("username") is not None, \
                "No username specified."

            # Update the user.
            user.set_attrs(attrs)

        except Exception as error:
            self.application.service.add_notification(
                make_datetime(), "Invalid field(s)", repr(error))
            self.redirect(fallback_page)
            return

        if self.try_commit():
            # Update the user on RWS.
            self.application.service.proxy_service.reinitialize()
        self.redirect(fallback_page)


class TeamHandler(BaseHandler):
    """Manage a single team.

    If referred by GET, this handler will return a pre-filled HTML form.
    If referred by POST, this handler will sync the team data with the form's.
    """
    def get(self, team_id):
        team = self.safe_get_item(Team, team_id)

        self.r_params = self.render_params()
        self.r_params["team"] = team
        self.render("team.html", **self.r_params)

    def post(self, team_id):
        fallback_page = "/team/%s" % team_id

        team = self.safe_get_item(Team, team_id)

        try:
            attrs = team.get_attrs()

            self.get_string(attrs, "code")
            self.get_string(attrs, "name")

            assert attrs.get("code") is not None, \
                "No team code specified."

            # Update the team.
            team.set_attrs(attrs)

        except Exception as error:
            self.application.service.add_notification(
                make_datetime(), "Invalid field(s)", repr(error))
            self.redirect(fallback_page)
            return

        if self.try_commit():
            # Update the team on RWS.
            self.application.service.proxy_service.reinitialize()
        self.redirect(fallback_page)


class AddTeamHandler(SimpleHandler("add_team.html", permission_all=True)):
    @require_permission(BaseHandler.PERMISSION_ALL)
    def post(self):
        fallback_page = "/teams/add"

        try:
            attrs = dict()

            self.get_string(attrs, "code")
            self.get_string(attrs, "name")

            assert attrs.get("code") is not None, \
                "No team code specified."

            # Create the team.
            team = Team(**attrs)
            self.sql_session.add(team)

        except Exception as error:
            self.application.service.add_notification(
                make_datetime(), "Invalid field(s)", repr(error))
            self.redirect(fallback_page)
            return

        if self.try_commit():
            # Create the team on RWS.
            self.application.service.proxy_service.reinitialize()

        # In case other teams need to be added.
        self.redirect(fallback_page)


class AddUserHandler(SimpleHandler("add_user.html", permission_all=True)):
    @require_permission(BaseHandler.PERMISSION_ALL)
    def post(self):
        fallback_page = "/users/add"

        try:
            attrs = dict()

            self.get_string(attrs, "first_name")
            self.get_string(attrs, "last_name")
            self.get_string(attrs, "username", empty=None)
            self.get_string(attrs, "password")
            self.get_string(attrs, "email")

            assert attrs.get("username") is not None, \
                "No username specified."

            self.get_string(attrs, "timezone", empty=None)

            self.get_string(attrs, "preferred_languages")

            # Create the user.
            user = User(**attrs)
            self.sql_session.add(user)

        except Exception as error:
            self.application.service.add_notification(
                make_datetime(), "Invalid field(s)", repr(error))
            self.redirect(fallback_page)
            return

        if self.try_commit():
            # Create the user on RWS.
            self.application.service.proxy_service.reinitialize()
            self.redirect("/user/%s" % user.id)
        else:
            self.redirect(fallback_page)


class AddParticipationHandler(BaseHandler):
    @require_permission(BaseHandler.PERMISSION_ALL)
    def post(self, user_id):
        fallback_page = "/user/%s" % user_id

        user = self.safe_get_item(User, user_id)

        try:
            contest_id = self.get_argument("contest_id")
            assert contest_id != "null", "Please select a valid contest"
        except Exception as error:
            self.application.service.add_notification(
                make_datetime(), "Invalid field(s)", repr(error))
            self.redirect(fallback_page)
            return

        self.contest = self.safe_get_item(Contest, contest_id)

        attrs = {}
        self.get_bool(attrs, "hidden")
        self.get_bool(attrs, "unrestricted")

        # Create the participation.
        participation = Participation(contest=self.contest,
                                      user=user,
                                      hidden=attrs["hidden"],
                                      unrestricted=attrs["unrestricted"])
        self.sql_session.add(participation)

        if self.try_commit():
            # Create the user on RWS.
            self.application.service.proxy_service.reinitialize()

        # Maybe they'll want to do this again (for another contest).
        self.redirect(fallback_page)


class EditParticipationHandler(BaseHandler):
    @require_permission(BaseHandler.PERMISSION_ALL)
    def post(self, user_id):
        fallback_page = "/user/%s" % user_id

        user = self.safe_get_item(User, user_id)

        try:
            contest_id = self.get_argument("contest_id")
            operation = self.get_argument("operation")
            assert contest_id != "null", "Please select a valid contest"
            assert operation in (
                "Remove",
            ), "Please select a valid operation"
        except Exception as error:
            self.application.service.add_notification(
                make_datetime(), "Invalid field(s)", repr(error))
            self.redirect(fallback_page)
            return

        self.contest = self.safe_get_item(Contest, contest_id)

        if operation == "Remove":
            # Remove the participation.
            participation = self.sql_session.query(Participation)\
                .filter(Participation.user == user)\
                .filter(Participation.contest == self.contest)\
                .first()
            self.sql_session.delete(participation)

        if self.try_commit():
            # Create the user on RWS.
            self.application.service.proxy_service.reinitialize()

        # Maybe they'll want to do this again (for another contest).
        self.redirect(fallback_page)
