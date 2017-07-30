#!/usr/bin/env python3
#
#  Heimdall Netcfg configures network (wireless) through Bluetooth
# 
#  Copyright (C) 2017 Christof Oost, Amir Shantia, Ron Snijders, Egbert van der Wal
#
#  This program is free software: you can redistribute it and/or modify
#  it under the terms of the GNU Affero General Public License as
#  published by the Free Software Foundation, either version 3 of the
#  License, or (at your option) any later version.
#
#  This program is distributed in the hope that it will be useful,
#  but WITHOUT ANY WARRANTY; without even the implied warranty of
#  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#  GNU Affero General Public License for more details.
#
#  You should have received a copy of the GNU Affero General Public License
#  along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
import os
import sys

if __name__ == "__main__":
    os.environ.setdefault("DJANGO_SETTINGS_MODULE", "netcfg.settings")

    from django.core.management import execute_from_command_line

    args = ['start.py', 'runserver', '0.0.0.0:8000', '--noreload']
    execute_from_command_line(args)
