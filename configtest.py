import unittest

import config


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


class ConfigTestCase(unittest.TestCase):
    def test_bad_config(self):
        """
        Test non-existent config file
        """
        missed_exception = False
        try:
            config.Config("test_data/test_bad_top_level.yml")
            missed_exception = True
        except Exception as e:
            if not e.message.startswith("Unrecognized top level entry in YAML file"):
                self.fail("Top level error generated unknown exception: " + e.message + e.strerror)
        if missed_exception:
            self.fail("Missed top level error in config")

    def test_soa_email(self):
        """
        Test config file with SOA_email
        """
        conf = config.Config("test_data/test_soa.yml")
        desired_zones = conf.get_desired_dns()
        self.assertNotEqual(None, desired_zones)
        self.assertEqual(1, len(desired_zones.keys()))
        self.check_zone_soa_email(desired_zones, 'zone1')

    def test_soa_email_with_family(self):
        """
        Test config file with SOA_email defined in the family, not in the zone
        """
        conf = config.Config("test_data/test_soa_from_family.yml")
        desired_zones = conf.get_desired_dns()
        self.assertNotEqual(None, desired_zones)
        self.assertEqual(1, len(desired_zones.keys()))
        self.check_zone_soa_email(desired_zones, 'zone1')

    def test_soa_email_with_family_and_zone(self):
        """
        Test SOA_email defined in both zone and family, get the one from zone
        """
        conf = config.Config("test_data/test_soa_from_family_and_zone.yml")
        desired_zones = conf.get_desired_dns()
        self.assertNotEqual(None, desired_zones)
        self.assertEqual(1, len(desired_zones.keys()))
        self.check_zone_soa_email(desired_zones, 'zone1')

    def test_seconds_email(self):
        """
        Test config file with four *_seconds fields
        """
        conf = config.Config("test_data/test_seconds.yml")
        desired_zones = conf.get_desired_dns()
        self.assertNotEqual(None, desired_zones)
        self.assertEqual(1, len(desired_zones.keys()))
        self.check_zone_seconds(desired_zones, 'zone1', 10, 11, 12, 13)

    def test_seconds_with_family(self):
        """
        Test config file with *_seconds defined in the family, not in the zone
        """
        conf = config.Config("test_data/test_seconds_from_family.yml")
        desired_zones = conf.get_desired_dns()
        self.assertNotEqual(None, desired_zones)
        self.assertEqual(1, len(desired_zones.keys()))
        self.check_zone_seconds(desired_zones, 'zone1', 20, 21, 22, 23)

    def test_seconds_with_family_and_zone(self):
        """
        Test *_seconds defined in both zone and family, get the one from zone
        """
        conf = config.Config("test_data/test_seconds_from_family_and_zone.yml")
        desired_zones = conf.get_desired_dns()
        self.assertNotEqual(None, desired_zones)
        self.assertEqual(1, len(desired_zones.keys()))
        self.check_zone_seconds(desired_zones, 'zone1', 10, 11, 12, 13)

    def test_nested_families(self):
        """
        Tests a zone that inherits from two families.
        """
        conf = config.Config("test_data/nested_families.yml")
        desired_zones = conf.get_desired_dns()
        self.assertNotEqual(None, desired_zones)
        self.assertEqual(1, len(desired_zones.keys()))
        self.check_zone_soa_email(desired_zones, 'domain.com')
        zone_to_test = desired_zones['domain.com']
        self.assertEqual(7, len(zone_to_test.records.keys()))
        self.check_record(zone_to_test, 'A', 'root', '1.1.1.1', None, 10)
        self.check_record(zone_to_test, 'A', 'shadow1', '1.1.1.2', None, 11)
        self.check_record(zone_to_test, 'A', 'shadow1', '1.1.1.4', None, 11)
        self.check_record(zone_to_test, 'A', 'shadow1', '1.1.1.5', None, 31)
        self.check_record(zone_to_test, 'A', 'shadow2', '1.1.1.3', None, 12)
        self.check_record(zone_to_test, 'A', 'family1', '2.1.1.1', None, 20)
        self.check_record(zone_to_test, 'A', 'family2', '3.1.1.1', None, 21)

    def test_empty_host(self):
        """
        Ensure empty host is an empty string, not None
        """
        conf = config.Config("test_data/empty.yml")
        desired_zones = conf.get_desired_dns()
        self.assertNotEqual(None, desired_zones)
        self.assertEqual(2, len(desired_zones.keys()))
        self.check_zone_soa_email(desired_zones, 'zone.com')
        self.check_zone_soa_email(desired_zones, 'zone2.com')
        zone_to_test = desired_zones['zone.com']
        self.assertEqual(['A::3.3.3.3'], sorted(zone_to_test.records.keys()))
        self.check_record(zone_to_test, 'A', '', '3.3.3.3', None, None)
        zone_to_test = desired_zones['zone2.com']
        self.assertEqual(['A::4.4.4.4'], sorted(zone_to_test.records.keys()))
        self.check_record(zone_to_test, 'A', '', '4.4.4.4', None, None)

    def test_a_records(self):
        """
        Test IPv4 and IPv6 generation of records
        """
        conf = config.Config("test_data/A_record_test.yml")
        desired_zones = conf.get_desired_dns()
        self.assertNotEqual(None, desired_zones)
        self.assertEqual(1, len(desired_zones.keys()))
        self.check_zone_soa_email(desired_zones, 'zone.com')
        zone_to_test = desired_zones['zone.com']
        self.assertEqual(['A:www1:3.3.3.3', 'A:www2:4.4.4.4', 'A:www4:1.1.1.1', 'A:www5:2.2.2.2', 'A:www7:1.2.3.4',
                          'A:www7:2.3.4.5', 'AAAA:www2:2600:3c00::1111', 'AAAA:www3:2600::2222',
                          'AAAA:www5:2600:3c00::f6e6:7287', 'AAAA:www6:2600:3c00::f6e6:7288'],
                         sorted(zone_to_test.records.keys()))
        self.check_record(zone_to_test, 'A', 'www1', '3.3.3.3', None, None)
        self.check_record(zone_to_test, 'A', 'www2', '4.4.4.4', None, None)
        self.check_record(zone_to_test, 'A', 'www4', '1.1.1.1', None, None)
        self.check_record(zone_to_test, 'A', 'www5', '2.2.2.2', None, None)
        self.check_record(zone_to_test, 'A', 'www7', '1.2.3.4', None, None)
        self.check_record(zone_to_test, 'A', 'www7', '2.3.4.5', None, None)
        self.check_record(zone_to_test, 'AAAA', 'www2', '2600:3c00::1111', None, None)
        self.check_record(zone_to_test, 'AAAA', 'www3', '2600::2222', None, None)
        self.check_record(zone_to_test, 'AAAA', 'www5', '2600:3c00::f6e6:7287', None, None)
        self.check_record(zone_to_test, 'AAAA', 'www6', '2600:3c00::f6e6:7288', None, None)

    def test_cname_records(self):
        """
        Test CNAME records, and expansion
        """
        conf = config.Config("test_data/CNAME_record_test.yml")
        desired_zones = conf.get_desired_dns()
        self.assertNotEqual(None, desired_zones)
        self.assertEqual(1, len(desired_zones.keys()))
        self.check_zone_soa_email(desired_zones, 'zone.com')
        zone_to_test = desired_zones['zone.com']
        self.assertEqual(['CNAME:www1:www.one.com', 'CNAME:www2:www.expansion.com', 'CNAME:www3:zone.com'],
                         sorted(zone_to_test.records.keys()))
        self.check_record(zone_to_test, 'CNAME', 'www1', 'www.one.com', None, None)
        self.check_record(zone_to_test, 'CNAME', 'www2', 'www.expansion.com', None, None)
        self.check_record(zone_to_test, 'CNAME', 'www3', 'zone.com', None, None)

    def test_cname_zone_expansion(self):
        """
        Test CNAME records that use families and have to expand {{ zone }}
        """
        conf = config.Config("test_data/CNAME_family_zone_expansion.yml")
        desired_zones = conf.get_desired_dns()
        self.assertNotEqual(None, desired_zones)
        self.assertEqual(1, len(desired_zones.keys()))
        self.check_zone_soa_email(desired_zones, 'zone.com')
        zone_to_test = desired_zones['zone.com']
        self.assertEqual(['CNAME:www:zone.com'], sorted(zone_to_test.records.keys()))
        self.check_record(zone_to_test, 'CNAME', 'www', 'zone.com', None, None)

    def test_txt_records(self):
        """
        Test TXT records and expansion
        """
        conf = config.Config("test_data/TXT_record_test.yml")
        desired_zones = conf.get_desired_dns()
        self.assertNotEqual(None, desired_zones)
        self.assertEqual(1, len(desired_zones.keys()))
        self.check_zone_soa_email(desired_zones, 'zone.com')
        zone_to_test = desired_zones['zone.com']
        self.assertEqual(['TXT:www1:foo', 'TXT:www2:expansion'], sorted(zone_to_test.records.keys()))
        self.check_record(zone_to_test, 'TXT', 'www1', 'foo', None, None)
        self.check_record(zone_to_test, 'TXT', 'www2', 'expansion', None, None)

    def test_mx_records(self):
        """
        Test MX records and expansion
        """
        conf = config.Config("test_data/MX_record_test.yml")
        desired_zones = conf.get_desired_dns()
        self.assertNotEqual(None, desired_zones)
        self.assertEqual(1, len(desired_zones.keys()))
        self.check_zone_soa_email(desired_zones, 'zone.com')
        zone_to_test = desired_zones['zone.com']
        self.assertEqual(['MX::mx1.foo.com'], sorted(zone_to_test.records.keys()))
        self.check_record(zone_to_test, 'MX', '', 'mx1.foo.com', 10, None)

    def check_zone_soa_email(self, zones, name):
        zone = zones[name]
        self.assertEqual(name, zone.domain)
        self.assertEqual('account@domain.com', zone.soa_email)

    def check_zone_seconds(self, zones, name, refresh_seconds, retry_seconds, expire_seconds, ttl_seconds):
        zone = zones[name]
        self.assertEqual(name, zone.domain)
        self.assertEqual(refresh_seconds, zone.refresh_seconds)
        self.assertEqual(retry_seconds, zone.retry_seconds)
        self.assertEqual(expire_seconds, zone.expire_seconds)
        self.assertEqual(ttl_seconds, zone.ttl_seconds)

    def check_record(self, zone, record_type, name, target, priority, ttl_seconds):
        key_name = record_type + ':' + name + ':' + target
        self.assertTrue(key_name in zone.records.keys())
        record = zone.records[key_name]
        self.assertEqual(record_type, record.record_type)
        self.assertEqual(name, record.name)
        self.assertEqual(target, record.target)
        self.assertEqual(priority, record.priority)
        self.assertEqual(ttl_seconds, record.ttl_seconds)


if __name__ == '__main__':
    unittest.main()
