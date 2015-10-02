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

from __future__ import absolute_import
from __future__ import print_function
from __future__ import unicode_literals

from cms.grading.scoretypes.GroupMin import GroupMin


# Dummy function to mark translatable string.
def N_(message):
    return message


class ICPC(GroupMin):
    """The score of a submission is 1 if it's correct, 0 otherwise.

    """
    TEMPLATE = ""

    def get_public_outcome(self, outcome, unused_parameter):
        """See ScoreTypeGroup."""
        if outcome > 0.5:
            return N_("Accepted")
        else:
            # TODO: here we should specify the type of error..?
            return N_("WA / TLE / MLE / RTE / ...")
