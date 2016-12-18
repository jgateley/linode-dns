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


import dns_record
import dns_zone
import socket
import yaml


class Config:
    """
    Class for creating zones/records from a YAML configuration file.
    A configuration YAML file looks like:
    ---
    IPs: ...
    FQDNs: ...
    TXTs: ...
    families: ...
    zones: ...

    The "IPs:" is a mapping from aliases to IP addresses, either IPv4, IPv6 or both.
    The mapping is used to expand target values for A records.
    See note below about how A records in the YAML file generate both A and AAAA records as needed
    Sample:
      foo: 1.2.3.4 2600::11aa
      bar: 2.3.4.5
      baz: 2600::22bb
    Here foo is an alias for both an IPv4 and IPv6 address, bar is a IPv4 alias, and baz an IPv6 alias

    The FQDNs is a mapping from aliases to fully qualified domain names.
    The mapping is used to expand target values in CNAME and MX records
    Sample:
      mx1: mx1.domain.com
      remote: remote-vpn.mycompany.com

    The TXTs is a mapping from aliases to text expansions.
    The mapping is used to expand target values in TXT records.
    Sample:
      spf: v=spf1 ip4:1.2.3.4  ip6:2600::4b4c -all
      dkim: v=DKIM1; k=rsa; p=MIGfMA0GC......

    families are dummy zones, containing both zone and record information, that are used to define families of hosts.
    For example, if you have several domains running on a single Apache web server, they'll all have the same
    DNS configuration (more or less). The family would defined the common entries, and then you would have a zone
    entry for each domain that references the family. Families have the same syntax as zones.

    zones are real zones, they contain both zone and record information. A zone is a mapping, and the following
    keys are valid:
    families: a list of names of families this zone belongs to.
    SOA_email: the SOA email address
    refresh_seconds:
    retry_seconds:
    expire_seconds:
    ttl_seconds:
    A, CNAME, MX, and TXT: lists of records.

    Records are mappings, and the following keys are valid:
    host, target, priority and ttl_seconds.
    For A records only, target can be a space separated list of IP addresses. If the address is IPv4, an A record
    is generated, and if IPv6 an AAAA record is generated. This makes it easier to handle hosts that are both
    IPv4 and IPv6 (very common nowadays).
    If the host is empty, Linode assumes you are referring to the whole domain.

    Example:
    ---
    IPs:
      foo: 1.2.3.4 2600::11aa
    FQDNs:
      mx1: mx1.domain.com
      remote: remote-vpn.mycompany.com
    TXTs: ...
      spf: v=spf1 ip4:1.2.3.4  ip6:2600::4b4c -all
      dkim: v=DKIM1; k=rsa; p=MIGfMA0GC......
    families:
      apache:
        SOA_email: webmaster@blah.com
        ttl_seconds: 3600
        A: [ { host: , target foo } ]
        CNAME: [ { host: www, target apache.domain.com ]
    zones:
      mydomain1:
        families: [ apache ]
        A: [ { host: dev, target 2.3.4.5, ttl_seconds: 3600 } ]
        MX: [ { host: , target: mx1, priority 10 } ]
        TXT:
          - { host: , target: spf }
          - { host: mail._domainkey, target: dkim }

    Object fields:
    raw_zones: the raw data from the YAML configuration file
    zones: raw_zones parsed into zones objects. (Mapping is from zone name to zone object)
    raw_families: the raw data from the YAML configuration file
    families: raw_families parsed into zones objects (Mapping is from family name to zone object)
    IPs: the IPs mapping
    FQDNs: the FQDNs mapping
    TXTs: the TXTs mapping.

    Usage;
    Create an object (passing in the config file name). The config file is parsed.
    Zone info is retrieved via the get_desired_dns method
    """

    def __init__(self, config_file_name):
        """
        Loads a config file and also parses it
        :param config_file_name:
        :return:
        :raises the parse function may raise an error
        """
        self.config_file_name = config_file_name
        with open(config_file_name) as yaml_file:
            self.yaml_data = yaml.safe_load(yaml_file)
        self.raw_zones = {}
        self.zones = {}
        self.raw_families = {}
        self.families = {}
        self.IPs = {}
        self.FQDNs = {}
        self.TXTs = {}
        self.parse()

    def parse(self):
        """
        Parses top level keys, and calls zone parsing as needed for zones and families
        :return:
        :raises error for unknown top level key, also zone errors
        """
        for top_level_key in self.yaml_data:
            if top_level_key == 'zones':
                self.raw_zones = self.yaml_data['zones']
            elif top_level_key == 'families':
                self.raw_families = self.yaml_data['families']
            elif top_level_key == 'IPs':
                self.IPs = self.yaml_data['IPs']
            elif top_level_key == 'FQDNs':
                self.FQDNs = self.yaml_data['FQDNs']
            elif top_level_key == "TXTs":
                self.TXTs = self.yaml_data['TXTs']
            else:
                raise Exception("Unrecognized top level entry in YAML file: " + top_level_key)
        for family_name in self.raw_families:
            self.families[family_name] = self.parse_zone(family_name, self.raw_families[family_name])
        for zone_name in self.raw_zones:
            self.zones[zone_name] = self.parse_zone(zone_name, self.raw_zones[zone_name])
            self.zones[zone_name].instantiate()

    def parse_zone(self, name, raw_zone):
        """
        Parses a zone
        :param name:
        :param raw_zone:
        :return:
        :raises error on bad zone top level key, or from record parsing
        """
        zone = dns_zone.Zone(name, None, None, None, None, None, None, None)
        for zone_key in raw_zone:
            if zone_key == 'SOA_email':
                zone.soa_email = raw_zone['SOA_email']
            elif zone_key == 'refresh_seconds':
                zone.refresh_seconds = raw_zone['refresh_seconds']
            elif zone_key == 'retry_seconds':
                zone.retry_seconds = raw_zone['retry_seconds']
            elif zone_key == 'expire_seconds':
                zone.expire_seconds = raw_zone['expire_seconds']
            elif zone_key == 'ttl_seconds':
                zone.ttl_seconds = raw_zone['ttl_seconds']
            elif zone_key in ['A', 'CNAME', 'MX', 'TXT', 'families']:
                pass
            else:
                raise Exception("Unrecognized zone key in YAML filefor zone " + name + ", key: " + zone_key)
        self.parse_records(zone, raw_zone, 'A')
        self.parse_records(zone, raw_zone, 'CNAME')
        self.parse_records(zone, raw_zone, 'MX')
        self.parse_records(zone, raw_zone, 'TXT')
        if 'families' in raw_zone:
            for family in raw_zone['families']:
                if not isinstance(family, str):
                    raise Exception("Family is not a string in zone: " + name)
                zone.merge(self.families[family])
        return zone

    def parse_records(self, zone, raw_zone, record_type):
        """
        Parse all records of a given type for a zone.
        :param zone: zone to put parsed records in
        :param raw_zone: raw data containing records to be parsed
        :param record_type: record type to look for
        :return: None
        :raises error from parse_record
        """
        if record_type in raw_zone:
            for raw_record in raw_zone[record_type]:
                if record_type == 'A':
                    self.parse_a_record(zone, raw_record)
                elif record_type == 'CNAME':
                    self.parse_cname_record(zone, raw_record)
                elif record_type == 'MX':
                    self.parse_mx_record(zone, raw_record)
                elif record_type == 'TXT':
                    self.parse_txt_record(zone, raw_record)
                else:
                    raise Exception("Unrecognized record type: " + record_type)

    def parse_a_record(self, zone, raw_record):
        """
        A records can generate several actual DNS records of type A or AAAA
        It depends on the IP address used.
        :param zone:
        :param raw_record:
        :return:
        """
        possible_alias = raw_record['target']
        if possible_alias in self.IPs:
            possible_alias = self.IPs[possible_alias]
        targets = possible_alias.split()
        for target in targets:
            if is_valid_ipv4_address(target):
                self.parse_record(zone, raw_record, 'A', target, {})
            elif is_valid_ipv6_address(target):
                self.parse_record(zone, raw_record, 'AAAA', target, {})
            else:
                raise Exception("Cannot parse IP address: " + target)

    def parse_cname_record(self, zone, raw_record):
        self.parse_record(zone, raw_record, 'CNAME', raw_record['target'], self.FQDNs)

    def parse_mx_record(self, zone, raw_record):
        self.parse_record(zone, raw_record, 'MX', raw_record['target'], self.FQDNs)

    def parse_txt_record(self, zone, raw_record):
        self.parse_record(zone, raw_record, 'TXT', raw_record['target'], self.TXTs)

    @staticmethod
    def parse_record(zone, raw_record, record_type, target, target_expansion):
        """
        Parse a single record for a zone.
        Special considerations:
        Missing host is replaced with an empty string
        Targets are expanded via dictionary
        :param zone: zone to put parsed records in
        :param raw_record: raw data containing record to be parsed
        :param record_type: record type to generate
        :param target: the target
        :param target_expansion: the dictionary used to possibly translate target
        :return: None
        """
        priority = None
        if 'priority' in raw_record:
            priority = raw_record['priority']
        host = raw_record['host']
        if host is None:
            host = ''
        ttl_seconds = None
        if 'ttl_seconds' in raw_record:
            ttl_seconds = raw_record['ttl_seconds']
        if target is None:
            target = ''
        if target in target_expansion:
            target = target_expansion[target]
        record = dns_record.Record(zone.domain, None, None, record_type, host, target, priority, ttl_seconds)
        zone.add_record(record)

    def get_desired_dns(self):
        return self.zones


def is_valid_ipv4_address(address):
    try:
        socket.inet_pton(socket.AF_INET, address)
    except AttributeError:  # no inet_pton here, sorry
        try:
            socket.inet_aton(address)
        except socket.error:
            return False
        return address.count('.') == 3
    except socket.error:  # not a valid address
        return False

    return True


def is_valid_ipv6_address(address):
    try:
        socket.inet_pton(socket.AF_INET6, address)
    except socket.error:  # not a valid address
        return False
    return True
