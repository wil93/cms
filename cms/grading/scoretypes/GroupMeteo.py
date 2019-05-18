#!/usr/bin/env python3

# Contest Management System - http://cms-dev.github.io/
# Copyright © 2010-2012 Giovanni Mascellani <mascellani@poisson.phc.unipi.it>
# Copyright © 2010-2018 Stefano Maggiolo <s.maggiolo@gmail.com>
# Copyright © 2010-2012 Matteo Boscariol <boscarim@hotmail.com>
# Copyright © 2019 William Di Luigi <williamdiluigi@gmail.com>
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

from . import ScoreTypeGroup


# Dummy function to mark translatable string.
def N_(message):
    return message


class GroupMeteo(ScoreTypeGroup):
    """Parameters are [[m, t, P1, P2], ... ] (see ScoreTypeGroup), where P1 is
    the threshold percentage of correct answers which separates "getting 0" from
    "getting a partial score", and P2 is the threshold percentage of correct
    answers which separates "getting a partial score" from "getting 100".

    In the original statement of the "METEO" task we have:

    - P1 = 0.15
    - P2 = 0.95
    """

    def get_public_outcome(self, outcome, parameter):
        """See ScoreTypeGroup."""
        if outcome <= 0.0:
            return N_("Not correct")
        elif outcome >= 1.0:
            return N_("Correct")
        else:
            return N_("Partially correct")

    def reduce(self, outcomes, parameter):
        """See ScoreTypeGroup."""
        P1 = parameter[2]
        P2 = parameter[3]

        correct = sum(outcomes)
        percentage = correct * 1.0 / len(outcomes)

        if percentage < P1:
            return 0.0
        elif percentage > P2:
            return 1.0
        else:
            return (percentage - 0.15) * 4.0 / 5.0
