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


class Record:
    """
    The Record class.
    domain_name: the name of the domain this record belongs to
    domain_id: the Linode ID of the domain, only filled in via the API, not for records in YAML configuration file
    resource_id: the Linode ID of the record, only filled in via the API
    record_type: "A", "AAAA", "CNAME", "MX", or "TXT"
    name: the host of the record
    target: the target of the record
    priority: the priority of the record, only used for MX
    ttl_seconds: the time to live seconds. 0 indicates default
    """
    def __init__(self, domain_name, domain_id, resource_id, record_type, name, target, priority, ttl_seconds):
        self.domain_name = domain_name
        self.domain_id = domain_id
        self.resource_id = resource_id
        self.record_type = record_type
        self.name = name
        self.target = target
        self.priority = priority
        self.ttl_seconds = None
        if ttl_seconds != 0:
            self.ttl_seconds = ttl_seconds


def from_json(json, domain_name):
    """
    Create a record object from the JSON returned from the Linode API
    :param json: JSON returned from Linode
    :param domain_name: Name of the domain/zone
    :return:
    """
    return Record(domain_name, json['DOMAINID'], json['RESOURCEID'], json['TYPE'], json['NAME'], json['TARGET'],
                  json['PRIORITY'], json['TTL_SEC'])
