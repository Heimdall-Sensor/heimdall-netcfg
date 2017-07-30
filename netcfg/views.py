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
import sys
sys.path.insert(0, '/usr/local/lib/python3.4/dist-packages')

from django.http import HttpResponse
from django.template import loader

import json
import uuid
from netcfg.lib.network2 import Network, Signals, SecretAgent2
import NetworkManager

import os

signal_handler = None
os.environ['NM_DEBUG'] = "1"

def get_signals():
    global signal_handler
    if signal_handler == None:
        signal_handler = Signals()
    return signal_handler

get_signals()

def index(request):
    template = loader.get_template('index.html');

    context = {}
    
    networks = Network.instance().get_wireless_networks()

    context['networks'] = sorted(networks, key=lambda score: score['strength'], reverse=True)

    for n in context['networks']:
        n['json'] = json.dumps(n)
    
    return HttpResponse(template.render(context, request))

def connect(request):
    essid = request.POST['essid'];
    key = request.POST['key'] if 'key' in request.POST else None

    known = Network.instance().get_known_connections()
    nets = Network.instance().get_wireless_networks()

    requested_net = None
    for net in nets:
        if net['essid'] == essid:
            requested_net = net

    if not requested_net:
        return HttpResponse(json.dumps({'error': 'Network %s is not available' % essid, 'essid': essid}), content_type='application/json')

    known_connection = Network.instance().find_connection(essid)
    target_ap = Network.instance().find_ap(essid)
    if not target_ap:
        return HttpResponse(json.dumps({'error': 'Network %s is not available' % essid, 'essid': essid}), content_type='application/json')

    # Connecting to an already known network?
    if 'known' in request.POST and request.POST['known'] == "true":
        if not known_connection:
            return HttpResponse(json.dumps({'error': 'Network %s is unknown' % essid, 'essid': essid}), content_type='application/json')
            
        # Just activate it
        wireless = Network.instance().get_device()
        print("We are now activiating the known connection")
        print("Known_connection: %s" % repr(known_connection))
        print("Wireless: %s" % repr(wireless))
        print("Target ap: %s" % repr(target_ap))
        NetworkManager.NetworkManager.ActivateConnection(known_connection, wireless, target_ap)

        return HttpResponse(json.dumps({'essid': essid, 'success': True}), content_type='application/json')

    known_config = None
    known_secrets = None
    if known_connection:
        known_config = known_connection.GetSettings()
        known_secrets = known_connection.GetSecrets()

    if not known_config:
        mode = request.POST['type'].lower()
        known_config = {
            u'802-11-wireless': {
                u'mode': mode,
                u'ssid': str(essid)
            },
            u'connection': {
                u'id': str(essid),
                u'type': '802-11-wireless',
                u'uuid': str(uuid.uuid4())
            },
            u'ipv4': {'method': 'auto'},
            u'ipv6': {'method': 'auto'}
        }

    enc = request.POST['encryption']
    if enc == "WEP":
        known_config[u'802-11-wireless'][u'security'] = u'802-11-wireless-security'
        known_config[u'802-11-wireless-security'] = {
            u'key-mgmt': u'none',
            u'wep-key-flags': 1,
            u'wep-key0': key
        }
    elif enc == "WPA-PSK" or enc == "WPA2-PSK":
        known_config[u'802-11-wireless'][u'security'] = u'802-11-wireless-security'
        known_config[u'802-11-wireless-security'] = {
            u'auth-alg': u'open',
            u'key-mgmt': u'wpa-psk',
            u'psk-flags': 1,
            u'psk': key
        }
    else:
        return HttpResponse(json.dumps({'essid': essid, 'error': 'Unsupported encryption: %s' % encryption}), content_type='application/json')

    if known_connection is None:
        known_connection = NetworkManager.Settings.AddConnection(known_config)
    else:
        known_connection.Update(known_config)

    secrets = SecretAgent2("/org/freedesktop/NetworkManager/SecretAgent") 
    sys.stderr.write("Saving to storage: %s\n" % repr(known_config))
    secrets.SaveSecrets(known_config, known_connection.object_path)

    # Now activate it
    wireless = Network.instance().get_device()
    NetworkManager.NetworkManager.ActivateConnection(known_connection, wireless, target_ap)

    return HttpResponse(json.dumps({'essid': essid, 'key': key, 'settings': known_config}), content_type='application/json')

def poll(request):
    response = {}
    response['networks'] = Network.instance().get_wireless_networks()

    s = get_signals()
    msg = s.get_last_messages()

    response['messages'] = []
    if msg:
        print(msg)
        response['messages'] += msg
        s.clear_messages()

    response['networks'] = sorted(response['networks'], key=lambda score: score['strength'], reverse=True)

    return HttpResponse(json.dumps(response), content_type='application/json') 
