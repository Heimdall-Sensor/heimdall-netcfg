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
from wicd.wnettools import BaseWirelessInterface
import wicd.dbusmanager as dbusmgr

import time

class Network(object):
    @classmethod
    def instance(cls):
        if not hasattr(cls, '_instance'):
            cls._instance = Network()

        return cls._instance

    def __init__(self):
        self.network_list = []
        self.network_stamp = 0
        self.dbus = None
        self.dbus_ifaces = None
        self.daemon = None
        self.wireless = None
        self.wired = None

    def setup(self):
        if self.wireless is not None:
            return

        dbusmgr.connect_to_dbus()
        self.dbus = dbusmgr.get_bus()
        self.dbus_ifaces = dbusmgr.get_dbus_ifaces()
        self.daemon = self.dbus_ifaces['daemon']
        self.wireless = self.dbus_ifaces['wireless']
        self.wired = self.dbus_ifaces['wired']

    def get_wireless_networks(self):
        current = time.time()
        if current - self.network_stamp < 2:
            return self.network_list

        self.setup()
        iwcfg = self.wireless.GetIwconfig()
        
        self.network_list = []
        for network_id in range(0, self.wireless.GetNumberOfNetworks()):
            is_active = self.wireless.GetCurrentSignalStrength("") != 0 and self.wireless.GetCurrentNetworkID(iwcfg) == network_id and self.wireless.GetWirelessIP('') is not None
        
            if self.daemon.GetSignalDisplayType() == 0:
                strenstr = 'quality'
                gap = 4 # Allow for 100%
            else:
                strenstr = 'strength'
                gap = 7 # -XX dbm = 7

            # All of that network property stuff
            strength = self.daemon.FormatSignalForPrinting(str(self.wireless.GetWirelessProperty(network_id, strenstr)))
            essid = self.wireless.GetWirelessProperty(network_id, 'essid')
            bssid = self.wireless.GetWirelessProperty(network_id, 'bssid')

            if self.wireless.GetWirelessProperty(network_id, 'encryption'):
                encrypt = self.wireless.GetWirelessProperty(network_id, 'encryption_method')
            else:
                encrypt = 'Unsecured'

            mode = self.wireless.GetWirelessProperty(network_id, 'mode') # Master, Ad-Hoc
            channel = self.wireless.GetWirelessProperty(network_id, 'channel')

            net = {'essid': str(essid), 'bssid': str(bssid), 'channel': int(str(channel)), 'mode': str(mode), 'strength': str(strength), 'encryption': str(encrypt)}
            self.network_list.append(net)

        self.network_stamp = time.time()
        return self.network_list

    def ssid_to_network_id(self, ssid):
        nets = self.get_wireless_networks()
        
        best_id = None
        best_strength = None

        for id, net in enumerate(nets):
            if net['essid'] == ssid:
                if best_strength is None or net['strength'] > best_strength:
                    best_strength = net['strength']
                    best_id = id
        
        return best_id

    def connect_to_ssid(self,ssid):
        network_id = self.ssid_to_network_id(ssid)
        if not network_id:
            return False

        return self.wireless.ConnectWireless(network_id)

    def connect_to_network(self, net):
        return self.connect_to_ssid(net['essid'])

    def get_current_network(self, net):
        return None

if __name__ == "__main__":
    import pprint
    nets = Network.instance().get_wireless_networks()
    pprint.pprint(nets)
