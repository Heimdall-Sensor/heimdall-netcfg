#!/bin/bash
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
#

/usr/sbin/hciconfig hci0 class 0x2A0430
/usr/sbin/hciconfig hci0 name heimdall4
/usr/sbin/hciconfig hci0 sspmode 0
/usr/sbin/hciconfig hci0 piscan

/usr/bin/bt-network -s nap -a hci0 pan0 &
~heimdall/netcfg/scripts/bluez-simple-agent &

exit 0
