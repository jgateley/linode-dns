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

import copy
import jinja2


class Zone:
    """
    Zone/domain object
    domain: the name of the zone/domain
    domain_id: the Linode ID of the zone, only filled in for objects via the API
    domain_type: master or slave
    soa_email: the email of the zone owner
    refresh_seconds: refresh seconds value
    retry_seconds: retry seconds value
    expire_seconds: expire seconds value
    ttl_seconds: time-to-live seconds value
    records: dictionary mapping record keys to records

    Record keys are the record type (A, AAAA, CNAME, MX or TXT), the host, and the target separated by colons

    All *_seconds values have 0 for default

    Zone records support replacing {{ zone }} with the zone name in CNAME target fields

    Zones support merging: A zone is merged with the zone representing a family when families are used
    """

    def __init__(self, domain, domain_id, domain_type, soa_email, refresh_seconds, retry_seconds, expire_seconds,
                 ttl_seconds):
        self.domain = domain
        self.domain_id = domain_id
        self.domain_type = domain_type
        self.soa_email = soa_email
        self.refresh_seconds = None
        if refresh_seconds != 0:
            self.refresh_seconds = refresh_seconds
        self.retry_seconds = None
        if retry_seconds != 0:
            self.retry_seconds = retry_seconds
        self.expire_seconds = None
        if expire_seconds != 0:
            self.expire_seconds = expire_seconds
        self.ttl_seconds = None
        if ttl_seconds != 0:
            self.ttl_seconds = ttl_seconds
        self.records = {}

    def add_record(self, record):
        """
        Adds a record, creating the key
        :param record: record to add
        :return: None
        """
        self.records[record.record_type + ':' + record.name + ':' + record.target] = record

    def instantiate(self):
        """ Replaces {{ zone }} with actual zone
        :return:
        """
        for record_key in self.records:
            record = self.records[record_key]
            if record.record_type == 'CNAME':
                self.records.pop(record_key)
                template = jinja2.Template(record.target)
                record.target = template.render(zone=self.domain)
                self.add_record(record)

    def merge(self, other):
        """
        Merge two zones. Used when doing families in the YAML configuration file, where a zone inherits values
        from families. The self zone is the master zone, and fields from other that don't exist in master are
        added to master. Fields that do exist are skipped. Records that don't exist in master and do exist in
        other are added to master. No record-leve merge takes place.
        :param other: zone to take missing values from
        :return: None
        """
        if self.soa_email is None and other.soa_email is not None:
            self.soa_email = other.soa_email
        if self.refresh_seconds is None and other.refresh_seconds is not None:
            self.refresh_seconds = other.refresh_seconds
        if self.retry_seconds is None and other.retry_seconds is not None:
            self.retry_seconds = other.retry_seconds
        if self.expire_seconds is None and other.expire_seconds is not None:
            self.expire_seconds = other.expire_seconds
        if self.ttl_seconds is None and other.ttl_seconds is not None:
            self.ttl_seconds = other.ttl_seconds
        existing_records = set(self.records.keys())
        other_records = set(other.records.keys())
        to_be_added = other_records - existing_records
        for record in to_be_added:
            self.add_record(copy.deepcopy(other.records[record]))


def from_json(json):
    return Zone(json['DOMAIN'], json['DOMAINID'], json['TYPE'], json['SOA_EMAIL'], json['REFRESH_SEC'],
                json['RETRY_SEC'], json['EXPIRE_SEC'], json['TTL_SEC'])
