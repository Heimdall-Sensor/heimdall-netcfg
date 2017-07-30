/*
  Heimdall Netcfg configures network (wireless) through Bluetooth
 
  Copyright (C) 2017 Christof Oost, Amir Shantia, Ron Snijders, Egbert van der Wal
 
  This program is free software: you can redistribute it and/or modify
  it under the terms of the GNU Affero General Public License as
  published by the Free Software Foundation, either version 3 of the
  License, or (at your option) any later version.
 
  This program is distributed in the hope that it will be useful,
  but WITHOUT ANY WARRANTY; without even the implied warranty of
  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
  GNU Affero General Public License for more details.
 
  You should have received a copy of the GNU Affero General Public License
  along with this program.  If not, see <http://www.gnu.org/licenses/>.
*/
 
var locked = false;

$(function () {
    $('#networks').on('click', 'tr', function () {
        selectNetwork($(this));
    });


    $('#refresh_nets').on('click', function () {
        poll();
        resetPollInterval();
    });

    $('#refresh_nets').button();

    resetPollInterval();
    poll();
});

function clearPollInterval()
{
    var ival = $('#networks').data('interval');
    if (ival)
    {
        clearInterval(ival);
        $('#networks').removeData('interval');
    }
}

function resetPollInterval()
{
    clearPollInterval();

    ival = setInterval(poll, 3000);
    $('#networks').data('interval', ival);
}

function poll()
{
    if (locked)
        return;

    $('#refresh_nets').prop('disabled', true);

    $.get('/poll', function (response) {
        $('#refresh_nets').prop('disabled', false);
        if (response.messages)
        {
            for (var idx = 0; idx < response.messages.length; ++idx)
                bsAlert(response.messages[idx]);
        }
        if (response.networks)
        {
            updateNetworkList(response.networks);
        }
    }, 'json');
}

function updateNetworkList(nets)
{
    var table = $('#networks');
    var tbody = table.children('tbody');

    tbody.detach();
    tbody.children().remove();

    for (var i = 0; i < nets.length; ++i)
    {
        var row = $('<tr></tr>');
        var select = $('<td></td>');
        var selector = $('<input type="radio" name="essid" />').attr('value', nets[i].essid);
        select.append(selector);

        if (nets[i].active)
            selector.prop('checked', true);

        var essid = $('<td></td>').text(nets[i].essid).addClass('essid');
        var bssid = $('<td></td>').text(nets[i].bssid).addClass('bssid');
        var channel = $('<td></td>').text(nets[i].channel).addClass('channel');
        var strength = $('<td></td>').text(nets[i].strength + '%').addClass('strength');
        var encryption = $('<td></td>').text(nets[i].encryption).addClass('encrypt');
        var type = $('<td></td>').text(nets[i].type).addClass('type');

        row.append(select, essid, bssid, channel, strength, encryption);
        row.data('details', nets[i]);
        tbody.append(row);
    }

    table.append(tbody);
}


function selectNetwork(tr)
{
    clearPollInterval();
    locked = true;

    tr.find('input[type=radio]').prop('checked', true);

    var network = tr.data('details');
    if (network.encryption != 'Unsecured' && network.known == false)
    {
        var key = prompt('Geef het WEP/WPA-wachtwoord op van het netwerk "' + network.essid + '"');
        if (!key)
        {
            // Reset radio button
            tr.find('input[type=radio]').prop('checked', false);

            $('#networks tbody tr').each(function () {
                var d = $(this).data('details');
                if (d.active)
                    $(this).find('input[type=radio]').prop('checked', true);
            });
            resetPollInterval();
            locked = false;
            return;
        }

        network.key = key;
    }

    $.post('/connect', network, function (response) {
        bsAlert('Er wordt nu verbinding gemaakt met ' + network.essid);
        resetPollInterval();
        locked = false;
    });
}

function bsAlert(msg, type)
{
    if (!type)
        type = 'info';

    $.bootstrapGrowl(msg, {
        ele: 'body',
        type: type,
        offset: {from: 'top', amount: 70},
        align: 'right',
        delay: 5000,
        stackup_spacing: 10
    });
}

function getCSRFToken(obj)
{
    if (document.cookie)
    {
        var cookies = document.cookie.split(';');
        for (var i = 0; i < cookies.length; ++i)
        {
            var cookie = $.trim(cookies[i]);
            // Does this cookie string begin with the name we want?
            if (cookie.substring(0, 10) == 'csrftoken=')
                return cookie.substring(10);
        }
    }
    return null;
}

function csrfSafeMethod(method)
{
    // these HTTP methods do not require CSRF protection
    return (/^(GET|HEAD|OPTIONS|TRACE)$/.test(method));
}

$.ajaxSetup({
    beforeSend: function(xhr, settings) {
        if (!csrfSafeMethod(settings.type) && !this.crossDomain) {
            xhr.setRequestHeader("X-CSRFToken", getCSRFToken());
        }
    }
});
