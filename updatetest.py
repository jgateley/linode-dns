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


import unittest

import dns_record
import dns_zone
import update


def delta_data():
    """
    Generates test data
    """
    global zone1, zone2, zone3, alternate_zone2
    zone1 = dns_zone.Zone('zone1', 1, 1, 'zone1@email.com', None, None, None, None)
    zone2 = dns_zone.Zone('zone2', 2, 2, 'zone2@email.com', 1, 1, 1, 1)
    zone2.add_record(dns_record.Record('zone2', 2, 22, 'A', 'a_record', '1.2.3.4', None, 1))
    zone2.add_record(dns_record.Record('zone2', 2, 23, 'AAAA', 'aaaa_record', '1.2.3.4', None, None))
    zone3 = dns_zone.Zone('zone3', 3, 3, 'zone3@email.com', None, None, None, None)
    alternate_zone2 = dns_zone.Zone('zone2', 2, 2, 'newzone2@email.com', 2, 2, 2, 2)
    alternate_zone2.add_record(dns_record.Record('zone2', 2, 22, 'A', 'a_record', '1.2.3.4', None, 2))
    alternate_zone2.add_record(dns_record.Record('zone2', 2, 24, 'CNAME', 'cname_record', '5.6.7.8', None, None))


class DeltaZonesTestCase(unittest.TestCase):
    def test_zones(self):
        """
        Basic list of zones test
        """
        delta_data()
        zones_delta = update.zones_delta({zone1.domain: zone1, zone2.domain: zone2},
                                         {alternate_zone2.domain: alternate_zone2, zone3.domain: zone3})
        self.assertEqual(3, len(zones_delta))
        self.assertEqual(1, len(zones_delta[0]))
        self.assertEqual(1, len(zones_delta[1]))
        self.assertEqual(1, len(zones_delta[2]))
        self.assertEqual('zone1', zones_delta[0][0])
        self.assertEqual('zone2', zones_delta[1][0])
        self.assertEqual('zone3', zones_delta[2][0])


class DeltaZoneTestCase(unittest.TestCase):
    def test_zone(self):
        """
        Test delta on a single zone
        """
        delta_data()
        zone_delta = update.zone_delta(zone2, alternate_zone2)
        self.assertEqual(['expire_seconds', 'refresh_seconds', 'retry_seconds', 'soa_email', 'ttl_seconds'],
                         sorted(zone_delta))


class DeltaRecordsTestCase(unittest.TestCase):
    def test_records(self):
        """
        Test delta on a list of records
        """
        delta_data()
        records_delta = update.records_delta(zone2.records, alternate_zone2.records)
        self.assertEqual(3, len(records_delta))
        self.assertEqual(1, len(records_delta[0]))
        self.assertEqual(1, len(records_delta[1]))
        self.assertEqual(1, len(records_delta[2]))
        self.assertEqual('AAAA:aaaa_record:1.2.3.4', records_delta[0][0])
        self.assertEqual('A:a_record:1.2.3.4', records_delta[1][0])
        self.assertEqual('CNAME:cname_record:5.6.7.8', records_delta[2][0])


class DeltaRecordTestCase(unittest.TestCase):
    def test_record(self):
        """
        Test delta on a single record
        """
        delta_data()
        record_delta = update.record_delta(zone2.records['A:a_record:1.2.3.4'],
                                           alternate_zone2.records['A:a_record:1.2.3.4'])
        self.assertEqual(['ttl_seconds'], record_delta)


if __name__ == '__main__':
    unittest.main()
