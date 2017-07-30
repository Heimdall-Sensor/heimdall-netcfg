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

/usr/bin/sudo /usr/bin/apt-get install libapache2-mod-xsendfile python3-dbus python3 python3-pip python3-dbus python3-yaml apache2-dev libdbus-1-dev libdbus-glib-1-dev
/usr/bin/sudo /usr/bin/pip3 install mod_wsgi
/usr/bin/sudo /usr/bin/pip3 install dbus-python
/usr/bin/sudo /usr/local/bin/mod_wsgi-express install-module
/bin/echo "LoadModule wsgi_module /usr/lib/apache2/modules/mod_wsgi-py34.cpython-34m.so" | /usr/bin/sudo /usr/bin/tee /etc/apache2/mods-available/wsgi.load
/bin/echo "WSGIPythonHome /usr" | /usr/bin/sudo /usr/bin/tee /etc/apache2/mods-available/wsgi.conf

/usr/bin/wget https://launchpad.net/ubuntu/+archive/primary/+files/libdbus-1-3_1.8.12-1ubuntu5_armhf.deb
/usr/bin/sudo dpkg -i libdbus-1-3_1.8.12-1ubuntu5_armhf.deb

/usr/bin/sudo /usr/sbin/a2enmod wsgi

/usr/bin/sudo /usr/bin/pip3 install django
cd /tmp
/usr/bin/wget https://pypi.python.org/packages/3c/08/bfa5b488dfeb310f11b774ad1568c8430574c5b43136abc3bde539c919da/python-networkmanager-1.0.1.tar.gz
/bin/tar xzvf python-networkanager-1.0.1.tar.gz
cd python-networkmanager-1.0.1
/usr/bin/sudo /usr/bin/python3 setup.py install

/usr/bin/sudo cp ~heimdall/netcfg/config/apache2/sites-available/000-default.conf /etc/apache2/sites-available/000-default.conf
/usr/bin/sudo /usr/sbin/service apache2 restart

/usr/bin/sudo cp ~heimdall/netcfg/config/.init_ros ~heimdall/.init_ros
/usr/bin/sudo chown heimdall:heimdall ~heimdall/.init_ros

/usr/bin/sudo /bin/chown heimdall:heimdall ~heimdall/netcfg/log 
/usr/bin/sudo /bin/chmod ugo+rwx ~heimdall/netcfg/log

/usr/bin/sudo cp ~heimdall/netcfg/config/dnsmasq.conf /etc/dnsmasq.d/pan0
