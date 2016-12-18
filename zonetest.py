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


class ConstructorTestCase(unittest.TestCase):
    def test_json(self):
        """
        Test creating a zone from JSON, as would happen when the API is invoked.
        Doesn't test records
        """
        zone = dns_zone.from_json({u'STATUS': 1, u'RETRY_SEC': 2, u'DOMAIN': u'jfoo.net', u'DOMAINID': 894758,
                                   u'TTL_SEC': 4, u'MASTER_IPS': u'', u'LPM_DISPLAYGROUP': u'',
                                   u'SOA_EMAIL': u'domains@jfoo.org', u'AXFR_IPS': u'none', u'REFRESH_SEC': 1,
                                   u'TYPE': u'master', u'EXPIRE_SEC': 3, u'DESCRIPTION': u''})
        self.assertEqual('jfoo.net', zone.domain)
        self.assertEqual(894758, zone.domain_id)
        self.assertEqual('master', zone.domain_type)
        self.assertEqual('domains@jfoo.org', zone.soa_email)
        self.assertEqual(1, zone.refresh_seconds)
        self.assertEqual(2, zone.retry_seconds)
        self.assertEqual(3, zone.expire_seconds)
        self.assertEqual(4, zone.ttl_seconds)

    def test_record(self):
        """
        Tests adding a record to a zone.
        """
        zone = dns_zone.from_json({u'STATUS': 1, u'RETRY_SEC': 0, u'DOMAIN': u'jfoo.net', u'DOMAINID': 894758,
                                   u'TTL_SEC': 0, u'MASTER_IPS': u'', u'LPM_DISPLAYGROUP': u'',
                                   u'SOA_EMAIL': u'domains@jfoo.org', u'AXFR_IPS': u'none', u'REFRESH_SEC': 0,
                                   u'TYPE': u'master', u'EXPIRE_SEC': 0, u'DESCRIPTION': u''})
        record = dns_record.from_json({u'DOMAINID': 894758, u'PROTOCOL': u'', u'TARGET': u'mx1.oustrencats.com',
                                       u'WEIGHT': 20, u'NAME': u'name', u'RESOURCEID': 7285261, u'PRIORITY': 0,
                                       u'TYPE': u'MX', u'PORT': 0, u'TTL_SEC': 0}, 'domain.com')
        zone.add_record(record)
        self.assertEqual(1, len(zone.records))

    def test_copy_record(self):
        """
        Tests a family record getting put in two zones, and later substitution could have unintended consequences
        """
        zone1 = dns_zone.from_json({u'STATUS': 1, u'RETRY_SEC': 0, u'DOMAIN': u'jfoo.net', u'DOMAINID': 894758,
                                    u'TTL_SEC': 0, u'MASTER_IPS': u'', u'LPM_DISPLAYGROUP': u'',
                                    u'SOA_EMAIL': u'domains@jfoo.org', u'AXFR_IPS': u'none', u'REFRESH_SEC': 0,
                                    u'TYPE': u'master', u'EXPIRE_SEC': 0, u'DESCRIPTION': u''})
        zone2 = dns_zone.from_json({u'STATUS': 1, u'RETRY_SEC': 0, u'DOMAIN': u'jfoo.org', u'DOMAINID': 894758,
                                    u'TTL_SEC': 0, u'MASTER_IPS': u'', u'LPM_DISPLAYGROUP': u'',
                                    u'SOA_EMAIL': u'domains@jfoo.org', u'AXFR_IPS': u'none', u'REFRESH_SEC': 0,
                                    u'TYPE': u'master', u'EXPIRE_SEC': 0, u'DESCRIPTION': u''})
        record = dns_record.from_json({u'DOMAINID': 894758, u'PROTOCOL': u'', u'TARGET': u'mx1.oustrencats.com',
                                       u'WEIGHT': 20, u'NAME': u'name', u'RESOURCEID': 7285261, u'PRIORITY': 0,
                                       u'TYPE': u'MX', u'PORT': 0, u'TTL_SEC': 0}, 'domain.com')
        zone1.add_record(record)
        zone2.merge(zone1)
        # This is a fragile test. Setting the target should also change the dictionary key
        zone1.records['MX:name:mx1.oustrencats.com'].target = 'mx2.oustrencats.com'
        self.assertEqual('mx2.oustrencats.com', zone1.records['MX:name:mx1.oustrencats.com'].target)
        self.assertEqual(u'mx1.oustrencats.com', zone2.records['MX:name:mx1.oustrencats.com'].target)


class MergeTestCase(unittest.TestCase):
    def test_soa_merge(self):
        """
        Tests merging two zones - the SOA e-mail.
        Tests merging when exists in both (merge doesn't happen,
        when only exists in other (merge happens),
        and when only exists in self (merge doesn't happen)
        """
        zone1 = dns_zone.Zone('zone1', None, 'master', 'email1@domain.com', None, None, None, None)
        zone2 = dns_zone.Zone('zone2', None, 'master', 'email2@domain.com', None, None, None, None)
        zone1.merge(zone2)
        self.assertEqual(zone1.soa_email, 'email1@domain.com')
        zone1 = dns_zone.Zone('zone1', None, 'master', None, None, None, None, None)
        zone2 = dns_zone.Zone('zone2', None, 'master', 'email2@domain.com', None, None, None, None)
        zone1.merge(zone2)
        self.assertEqual(zone1.soa_email, 'email2@domain.com')
        zone1 = dns_zone.Zone('zone1', None, 'master', 'email1@domain.com', None, None, None, None)
        zone2 = dns_zone.Zone('zone2', None, 'master', None, None, None, None, None)
        zone1.merge(zone2)
        self.assertEqual(zone1.soa_email, 'email1@domain.com')

    def test_ttl_seconds_merge(self):
        """
        Tests merging two zones - the ttl_seconds.
        Tests merging when exists in both (merge doesn't happen,
        when only exists in other (merge happens),
        and when only exists in self (merge doesn't happen)
        """
        zone1 = dns_zone.Zone('zone1', None, 'master', 'email1@domain.com', None, None, None, 10)
        zone2 = dns_zone.Zone('zone2', None, 'master', 'email2@domain.com', None, None, None, 20)
        zone1.merge(zone2)
        self.assertEqual(zone1.ttl_seconds, 10)
        zone1 = dns_zone.Zone('zone1', None, 'master', 'email1@domain.com', None, None, None, None)
        zone2 = dns_zone.Zone('zone2', None, 'master', 'email2@domain.com', None, None, None, 20)
        zone1.merge(zone2)
        self.assertEqual(zone1.ttl_seconds, 20)
        zone1 = dns_zone.Zone('zone1', None, 'master', 'email1@domain.com', None, None, None, 10)
        zone2 = dns_zone.Zone('zone2', None, 'master', 'email2@domain.com', None, None, None, None)
        zone1.merge(zone2)
        self.assertEqual(zone1.ttl_seconds, 10)

    def test_records_merge(self):
        """
        Tests merging records of two zones. A:www and A:www2 exist in self. A:www2 and A:www3 exist in other.
        Result should be A:www, A:www2 from self, and A:www3 from other
        """
        zone1 = dns_zone.Zone('zone1', None, 'master', 'account@domain.com', None, None, None, None)
        zone2 = dns_zone.Zone('zone1', None, 'master', 'account@domain.com', None, None, None, None)
        record1 = dns_record.Record('zone1', None, None, 'A', 'www', 'foo', None, None)
        record2 = dns_record.Record('zone1', None, None, 'A', 'www2', 'foo', None, 10)
        record3 = dns_record.Record('zone1', None, None, 'A', 'www2', 'foo', None, 20)
        record4 = dns_record.Record('zone1', None, None, 'A', 'www3', 'bar', None, None)
        zone1.add_record(record1)
        zone1.add_record(record2)
        zone2.add_record(record3)
        zone2.add_record(record4)
        zone1.merge(zone2)
        self.assertEqual(3, len(zone1.records))
        result1 = zone1.records['A:www:foo']
        result2 = zone1.records['A:www2:foo']
        result3 = zone1.records['A:www3:bar']
        self.assertEqual('foo', result1.target)
        self.assertEqual('foo', result2.target)
        self.assertEqual(10, result2.ttl_seconds)
        self.assertEqual('bar', result3.target)


if __name__ == '__main__':
    unittest.main()
