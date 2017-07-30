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
from __future__ import print_function

from dbus.mainloop.glib import DBusGMainLoop
DBusGMainLoop(set_as_default=True)

import NetworkManager as NM
from gi.repository import GLib
import struct
import pprint
import time
from threading import Thread
import sys
import os

class Network(object):
    @classmethod
    def instance(cls):
        if not hasattr(cls, '_instance'):
            cls._instance = Network()

        return cls._instance

    def __init__(self):
        self.network_stamp = 0
        self.connection_stamp = 0

    def get_device(self):
        for dev in NM.NetworkManager.GetDevices():
            try:
                iface = dev.SpecificDevice()
            except KeyError as e:
                # No interest in unsupported device types
                continue

            if isinstance(iface, NM.Wireless):
                return iface

        return None

    def find_ap(self, essid):
        for dev in NM.NetworkManager.GetDevices():
            iface = None
            try:
                iface = dev.SpecificDevice()
            except KeyError as e:
                # No interest in unsupported device types
                continue

            if isinstance(iface, NM.Wireless):
                for net in iface.GetAccessPoints():
                    if net.Ssid == essid:
                        return net

    def find_connection(self, essid):
        conns = NM.Settings.ListConnections()
        for conn in conns:
            s = conn.GetSettings()
            if not u'802-11-wireless' in s or \
               not u'ssid' in s[u'802-11-wireless']:
                continue

            if s[u'802-11-wireless'][u'ssid'] == essid:
                return conn

        return None

    def get_known_connections(self):
        current = time.time()
        if current - self.connection_stamp < 2:
            return self.connection_list

        self.connection_list = []
        conns = NM.Settings.ListConnections()
        for conn in conns:
            settings = conn.GetSettings()
            if settings['connection']['type'] == u'802-11-wireless':
                sec = None
                if settings[u'802-11-wireless'][u'security'] == u'802-11-wireless-security':
                    sec = settings[u'802-11-wireless-security'][u'key-mgmt']
                self.connection_list.append({
                    'id': settings[u'connection'][u'id'],
                    'essid': settings[u'802-11-wireless'][u'ssid'],
                    'mode': settings[u'802-11-wireless'][u'mode'],
                    'security': sec
                })

        return self.connection_list
    
    def get_wireless_networks(self):
        current = time.time()
        if current - self.network_stamp < 2:
            return self.network_list

        known = self.get_known_connections()
        self.network_list = []
        for dev in NM.NetworkManager.GetDevices():
            iface = None
            active = dev.ActiveConnection
            try:
                iface = dev.SpecificDevice()
            except KeyError as e:
                # No interest in unsupported device types
                continue

            if isinstance(iface, NM.Wireless):
                if active:
                    try:
                        active = active.Connection.GetSettings()['802-11-wireless']['ssid']
                    except Exception as e:
                        active = None
                else:
                    active = None

                for net in iface.GetAccessPoints():
                    is_known = False
                    for knet in known:
                        if knet['essid'] == net.Ssid:
                            is_known = True

                    v = int(net.Strength)
                    # (v, ) = struct.unpack('!b', strength)

                    if not net.Flags & NM.NM_802_11_AP_FLAGS_PRIVACY:
                        enc = "Unsecured"
                    else:
                        enc = "WEP"

                    if net.RsnFlags & NM.NM_802_11_AP_SEC_PAIR_CCMP:
                        enc = "WPA2"
                    elif net.WpaFlags & NM.NM_802_11_AP_SEC_PAIR_TKIP:
                        enc = "WPA"

                    if net.RsnFlags & NM.NM_802_11_AP_SEC_KEY_MGMT_PSK or \
                        net.WpaFlags & NM.NM_802_11_AP_SEC_KEY_MGMT_PSK:
                        enc += "-PSK"
                    elif net.RsnFlags & NM.NM_802_11_AP_SEC_KEY_MGMT_802_1X or \
                        net.WpaFlags & NM.NM_802_11_AP_SEC_KEY_MGMT_802_1X:
                        enc += "-802.1X"

                    channel = net.Frequency
                    if channel > 2400 and channel < 2500:
                        channel = (channel - 2407) / 5
                    elif channel > 5000:
                        channel = (channel - 5000) / 5

                    mode = "Unknown"
                    if net.Mode == NM.NM_802_11_MODE_ADHOC:
                        mode = "AdHoc"
                    elif net.Mode == NM.NM_802_11_MODE_INFRA:
                        mode = "Infrastructure"

                    self.network_list.append({
                        'essid': net.Ssid,
                        'bssid': net.HwAddress,
                        'active': net.Ssid == active,
                        'known': is_known,
                        'mode': net.Mode,
                        'strength': v,
                        'frequency': net.Frequency,
                        'channel': channel,
                        'encryption': enc,
                        'Flags': "0x%0.3X" % net.Flags,
                        'Wpaflags': "0x%0.3X" % net.WpaFlags,
                        'RsnFlags': "0x%0.3X" % net.RsnFlags,
                        'type': mode
                    })

        self.network_stamp = time.time()
        return self.network_list

class Signals(Thread):
    def __init__(self):
        super(Signals, self).__init__()
        self.alive = True
        self.setDaemon(True)
        self.start()

        self.last_messages = []

    def run(self):
        print("Starting glib mainloop")
        self.mainloop = GLib.MainLoop()
        self.wait_for_signals(self.mainloop)
        try:
            self.mainloop.run()
        except KeyboardInterrupt:
            print("Caught signal SIGINT - shutting down")
            import _thread
            print("Interrupting main thread")
            _thread.interrupt_main()
            raise
        self.alive = False

    def is_alive(self):
        return self.alive and super(Signals, self).is_alive()

    def wait_for_signals(self, mainloop):
        for dev in NM.NetworkManager.GetDevices():
            dev.connect_to_signal("StateChanged", self.on_state_changed, 
                sender_keyword='sender',
                destination_keyword='dest',
                interface_keyword='iface',
                member_keyword='member',
                path_keyword='path')
                
    def on_state_changed(self, new_state, old_state, reason, **kwargs):
        object_path = str(kwargs['path'])
        dev = NM.Device(object_path)
        iface = str(dev.Interface)
        reason = NM.const('DEVICE_STATE_REASON', reason)

        if   new_state == NM.NM_DEVICE_STATE_UNKNOWN:
            self.last_messages.append("Interface '%s' is an unknown state" % iface)
        elif new_state == NM.NM_DEVICE_STATE_UNMANAGED:
            self.last_messages.append("Interface '%s' is unmanaged")
        elif new_state == NM.NM_DEVICE_STATE_UNAVAILABLE:
            self.last_messages.append("Interface '%s' is unavailable: %s" % reason)
        elif new_state == NM.NM_DEVICE_STATE_DISCONNECTED:
            self.last_messages.append("Interface '%s' is disconnecteds" % reason)
        elif new_state == NM.NM_DEVICE_STATE_PREPARE:
            self.last_messages.append("Preparing interface '%s'" % iface)
        elif new_state == NM.NM_DEVICE_STATE_CONFIG:
            self.last_messages.append("Configuring interface '%s'" % iface)
        elif new_state == NM.NM_DEVICE_STATE_NEED_AUTH:
            self.last_messages.append("Authentication required on interface '%s'" % iface)
        elif new_state == NM.NM_DEVICE_STATE_IP_CONFIG:
            self.last_messages.append("Configuring IP-address on interface '%s'" % iface)
        elif new_state == NM.NM_DEVICE_STATE_IP_CHECK:
            self.last_messages.append("Checking IP-address on interface '%s'" % iface)
        elif new_state == NM.NM_DEVICE_STATE_SECONDARIES:
            self.last_messages.append("Waiting for secondary connections on interface '%s'" % iface)
        elif new_state == NM.NM_DEVICE_STATE_ACTIVATED:
            self.last_messages.append("Interface '%s' has been activated" % iface)
        elif new_state == NM.NM_DEVICE_STATE_DEACTIVATING:
            self.last_messages.append("Inteface '%s' is deactivating: %s" % (iface, reason))
        elif new_state == NM.NM_DEVICE_STATE_FAILED:
            self.last_messages.append("Connection on interface '%s' failed: %s" % (iface, reason))

        print(repr(self.last_messages))

    def stop(self):
        self.mainloop.quit()

    def get_last_messages(self):
        print("Last received message: %s" % self.last_messages)
        return self.last_messages

    def clear_messages(self):
        self.last_messages = []

if __name__ == '__main__':
    n = Network()
    nets = n.get_wireless_networks()
    print("%d wireless networks visible" % len(nets))

    s = Signals()
    try:
        while s.is_alive():
            time.sleep(1)
    except KeyboardInterrupt:
        print("Interrupted")
        ml.stop()

class SecretAgent2(NM.NMDbusInterface):
    interface_name = 'org.freedesktop.NetworkManager.SecretAgent'

    def preprocess(self, name, args, kwargs):
        sys.stderr.write((repr(name) + '\n'))
        if name in ('SaveSecrets'):
            settings = args[0]
            for key in settings:
                if 'mac-address' in settings[key]:
                    settings[key]['mac-address'] = NM.fixups.mac_to_dbus(settings[key]['mac-address'])
                if 'cloned-mac-address' in settings[key]:
                    settings[key]['cloned-mac-address'] = NM.fixups.mac_to_dbus(settings[key]['cloned-mac-address'])
                if 'bssid' in settings[key]:
                    settings[key]['bssid'] = NM.fixups.mac_to_dbus(settings[key]['mac-address'])
            if 'ssid' in settings.get('802-11-wireless', {}):
                settings['802-11-wireless']['ssid'] = NM.fixups.ssid_to_dbus(settings['802-11-wireless']['ssid'])
            if 'ipv4' in settings:
                if 'addresses' in settings['ipv4']:
                    settings['ipv4']['addresses'] = [NM.fixups.addrconf_to_dbus(addr,socket.AF_INET) for addr in settings['ipv4']['addresses']]
                if 'routes' in settings['ipv4']:
                    settings['ipv4']['routes'] = [NM.fixups.route_to_dbus(route,socket.AF_INET) for route in settings['ipv4']['routes']]
                if 'dns' in settings['ipv4']:
                    settings['ipv4']['dns'] = [NM.fixups.addr_to_dbus(addr,socket.AF_INET) for addr in settings['ipv4']['dns']]
            if 'ipv6' in settings:
                if 'addresses' in settings['ipv6']:
                    settings['ipv6']['addresses'] = [NM.fixups.addrconf_to_dbus(addr,socket.AF_INET6) for addr in settings['ipv6']['addresses']]
                if 'routes' in settings['ipv6']:
                    settings['ipv6']['routes'] = [NM.fixups.route_to_dbus(route,socket.AF_INET6) for route in settings['ipv6']['routes']]
                if 'dns' in settings['ipv6']:
                    settings['ipv6']['dns'] = [NM.fixups.addr_to_dbus(addr,socket.AF_INET6) for addr in settings['ipv6']['dns']]
        return args, kwargs

    def SaveSecrets(self, connection, connection_path):
        sys.stderr.write(repr(connection) + '\n')
        sys.stderr.write(repr(connection_path) + '\n')
        return self.make_proxy_call('SaveSecrets')(connection, connection_path, signature='a{sa{sv}}o')
