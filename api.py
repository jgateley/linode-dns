# Copyright (c) 2016 John Gateley

# Permission is hereby granted, free of charge, to any person obtaining a copy of this software and associated
# documentation files (the "Software"), to deal in the Software without restriction, including without limitation
# the rights to use, copy, modify, merge, publish, distribute, sublicense, and/or sell copies of the Software,
# and to permit persons to whom the Software is furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in all copies or substantial portions
# of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED
# TO THE WARRANTIES OF MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL
# THE AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION OF
# CONTRACT, TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER
# DEALINGS IN THE SOFTWARE.


import requests
import urllib


class Api:
    """
    Api is a class that accesses the Linode API for DNS. It is a simple wrapper of the raw API
    except that it translates dns_zone and dns_record objects into the syntax of the API.
    It supports "dry run"ing, which allows query operations, but prints what would happen for modifying operations.
    """

    def __init__(self, key, dry_run):
        """
        :param key: the Linode API key
        :param dry_run: True means do not apply changes, just print out what changes
        :return: Api object
        """
        self.url = 'https://api.linode.com/?api_key=' + key + '&api_action='
        self.dry_run = dry_run

    def call(self, action, arguments):
        """
        Private function, does an API call.
        Note that the API key is built into the URL.
        Note that URL quoting is important, especially for TXT records that can have escapable characters
        :param action: Linode call name
        :param arguments: dictionary of name/value pairs
        :return: The result of the call if successful
        :raises: an error if the call fails
        """
        argument_list = []
        for argument in arguments:
            argument_list.append(argument + "=" + urllib.quote_plus(str(arguments[argument])))
        url = self.url + action
        if argument_list:
            url = url + "&" + "&".join(argument_list)
        response = requests.get(url).json()
        if response['ERRORARRAY']:
            raise Exception("API call failed: " + response['ERRORARRAY'][0]['ERRORMESSAGE'])
        return response['DATA']

    def list_zones(self):
        """
        Linode domain.list call
        :return: list of all domains
        """
        return self.call('domain.list', {})

    def add_zone(self, zone):
        """
        Linode domain.create call
        :param zone: zone to create
        :return: None
        """
        print "Adding new zone " + zone.domain
        if not self.dry_run:
            result = self.call('domain.create', {'Domain': zone.domain, 'Type': 'master', 'SOA_Email': zone.soa_email})
            zone.domain_id = result['DomainID']

    def delete_zone(self, zone):
        """
        Linode domain.delete call
        :param zone: zone to delete (DomainID must be filled in)
        :return: None
        """
        print "Deleting entire zone " + zone.domain
        if not self.dry_run:
            self.call('domain.delete', {'DomainID': zone.domain_id})

    def modify_zone(self, zone, desired, fields):
        """
        Linode domain.update call. Fields are the fields to change.
        :param zone: zone to change
        :param desired: zone object containing desired values
        :param fields: names of the fields to change
        :return: None
        """
        if len(fields) == 0:
            return
        print "Modifying zone " + zone.domain
        args = {'DomainID': zone.domain_id}
        for field in fields:
            print "  Field " + field + " changes from " + str(getattr(zone, field)) + " to "\
                  + str(getattr(desired, field))
            args[field] = getattr(desired, field)
        if not self.dry_run:
            self.call('domain.update', args)

    def list_records(self, zone):
        """
        Linode domain.resource.list call (record list)
        :param zone: zone to list (domain ID must exist)
        :return: list of records
        """
        return self.call('domain.resource.list', {'DomainID': zone.domain_id})

    def add_record(self, zone, record):
        """
        Linode domain.resource.create call (create a record)
        :param zone: zone in which to create the new record (domain ID must exist)
        :param record: record to create
        :return: None
        """
        print 'Adding new record (in zone ' + zone.domain + ') of type ' + record.record_type + ' with name '\
              + record.name + ', target ' + record.target + ', and priority ' + str(record.priority)
        if not self.dry_run:
            args = {'DomainID': zone.domain_id, 'Type': record.record_type, 'Name': record.name,
                    'Target': record.target}
            if record.record_type == 'MX':
                args['Priority'] = record.priority
            self.call('domain.resource.create', args)

    def delete_record(self, record):
        """
        Linode domain.resource.delete call (delete a record)
        :param record: record to delete (DomainID and Resource ID must both exist)
        :return: None
        """
        print 'Deleting record (in zone ' + record.domain_name + "): " + record.record_type + ' named ' + record.name\
              + ', target ' + record.target + ', and priority ' + str(record.priority)
        if not self.dry_run:
            self.call('domain.resource.delete', {'DomainID': record.domain_id, 'ResourceID': record.resource_id})

    def modify_record(self, record, desired, fields):
        """
        Linode domain.resource.update call (modify a record)
        :param record: record to modify, DomainID and ResourceID must both exist
        :param desired: record containing values desired
        :param fields: Names of fields to change
        :return: None
        """
        if len(fields) == 0:
            return
        print "Modifying record (in zone " + record.domain_name + ") " + record.record_type + " " + record.name
        args = {'DomainID': record.domain_id, 'ResourceID': record.resource_id}
        for field in fields:
            print "  Field " + field + " changes from " + str(getattr(record, field))\
                  + " to " + str(getattr(desired, field))
            args[field] = getattr(desired, field)
        if not self.dry_run:
            self.call('domain.resource.update', args)
