#!/usr/bin/python

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


"""
The main program
Reads the Linode configuration, gets the YAML desired configuration.
Computes the delta, and applies it.
"""


import api
import argparse
import config
import dns_record
import dns_zone


def get_linode_dns(linode_api):
    """ Get the existing zone configuration from Linode
    :param linode_api: The API object
    :return: dictionary of zones
    """
    linode_zones = {}
    json_zones = linode_api.list_zones()
    for json_zone in json_zones:
        zone = dns_zone.from_json(json_zone)
        linode_zones[zone.domain] = zone
        json_records = linode_api.list_records(zone)
        for json_record in json_records:
            record = dns_record.from_json(json_record, zone.domain)
            zone.add_record(record)
    return linode_zones


def dictionary_delta(existing_dict, desired_dict):
    """ Compute the delta between two dictionaries
    :param existing_dict:
    :param desired_dict:
    :return:
    """
    existing_keys = set(existing_dict.keys())
    desired_keys = set(desired_dict.keys())
    to_be_deleted = existing_keys - desired_keys
    to_be_added = desired_keys - existing_keys
    to_be_changed = existing_keys - to_be_deleted
    return [list(to_be_deleted), list(to_be_changed), list(to_be_added)]


def zones_delta(existing_zones, desired_zones):
    """ Compute the delta between two lists of zones.
    Only does zones to be added, deleted, and zones to be checked for differences
    Does not recur into zones that need to be checked.
    :param existing_zones:
    :param desired_zones:
    :return:
    """
    return dictionary_delta(existing_zones, desired_zones)


def zone_delta(existing_zone, desired_zone):
    """ Figure out which fields have changed between an existing and desired zone
    :param existing_zone:
    :param desired_zone:
    :return:
    """
    changed_fields = []
    if existing_zone.soa_email != desired_zone.soa_email:
        changed_fields.append('soa_email')
    if existing_zone.refresh_seconds != desired_zone.refresh_seconds:
        changed_fields.append('refresh_seconds')
    if existing_zone.retry_seconds != desired_zone.retry_seconds:
        changed_fields.append('retry_seconds')
    if existing_zone.expire_seconds != desired_zone.expire_seconds:
        changed_fields.append('expire_seconds')
    if existing_zone.ttl_seconds != desired_zone.ttl_seconds:
        changed_fields.append('ttl_seconds')
    return changed_fields


def records_delta(existing_records, desired_records):
    """ Figures out delta for two groups of records
    :param existing_records:
    :param desired_records:
    :return:
    """
    return dictionary_delta(existing_records, desired_records)


def record_delta(existing_record, desired_record):
    """ Figures out delta for a single record
    :param existing_record:
    :param desired_record:
    :return:
    """
    changed_fields = []
    if existing_record.name != desired_record.name:
        changed_fields.append('name')
    if existing_record.target != desired_record.target:
        changed_fields.append('target')
    if (existing_record.priority != desired_record.priority) and (existing_record.record_type == 'MX'):
        changed_fields.append('priority')
    if existing_record.ttl_seconds != desired_record.ttl_seconds:
        changed_fields.append('ttl_seconds')
    return changed_fields


def apply_delta(api_key, config_file, dry_run):
    """
    Loads the Linode configuration (aka existing)
    Loads the YAML configuration (aka desired)
    Computes the zones to be added, deleted and modified.
    Deletes the zones as needed
    Adds the zones as needed
    Computes the changes for each zone that needs to be modified
    Computes the record changes for each zone that needs to be modified
    :param api_key:
    :param config_file:
    :param dry_run:
    :return:
    """
    linode_api = api.Api(api_key, dry_run)
    existing = get_linode_dns(linode_api)
    desired = config.Config(config_file).get_desired_dns()
    changes = zones_delta(existing, desired)
    to_be_deleted = changes[0]
    to_be_updated = changes[1]
    to_be_added = changes[2]
    for zone in to_be_deleted:
        linode_api.delete_zone(existing[zone])
    for zone in to_be_updated:
        field_changes = zone_delta(existing[zone], desired[zone])
        linode_api.modify_zone(existing[zone], desired[zone], field_changes)
        record_changes = records_delta(existing[zone].records, desired[zone].records)
        records_to_be_deleted = record_changes[0]
        records_to_be_updated = record_changes[1]
        records_to_be_added = record_changes[2]
        for record in records_to_be_deleted:
            linode_api.delete_record(existing[zone].records[record])
        for record in records_to_be_updated:
            field_changes = record_delta(existing[zone].records[record], desired[zone].records[record])
            linode_api.modify_record(existing[zone].records[record], desired[zone].records[record], field_changes)
        for record in records_to_be_added:
            linode_api.add_record(existing[zone], desired[zone].records[record])
    for zone in to_be_added:
        linode_api.add_zone(desired[zone])
        for record_name in desired[zone].records.keys():
            linode_api.add_record(desired[zone], desired[zone].records[record_name])


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description="Update Linode DNS configuration to match specification")
    parser.add_argument('api_key', help='Linode API key')
    parser.add_argument('config_file', help='Config file with desired DNS specification')
    parser.add_argument('-d', "--dryrun", action="store_true", help='Print changes on STDOUT, but do not execute them')
    args = parser.parse_args()

    apply_delta(args.api_key, args.config_file, args.dryrun)
