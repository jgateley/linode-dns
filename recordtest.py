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


class ConstructorTestCase(unittest.TestCase):
    def test_json(self):
        """
        Tests creating a record from JSON, like would happen when the API is used.
        """
        record = dns_record.from_json({u'DOMAINID': 894758, u'PROTOCOL': u'', u'TARGET': u'mx1.oustrencats.com',
                                       u'WEIGHT': 20, u'NAME': u'name', u'RESOURCEID': 7285261, u'PRIORITY': 30,
                                       u'TYPE': u'MX', u'PORT': 0, u'TTL_SEC': 0}, 'domain.com')
        self.assertEqual(894758, record.domain_id)
        self.assertEqual(7285261, record.resource_id)
        self.assertEqual('MX', record.record_type)
        self.assertEqual('name', record.name)
        self.assertEqual('mx1.oustrencats.com', record.target)
        self.assertEqual(30, record.priority)
        self.assertEqual(None, record.ttl_seconds)


if __name__ == '__main__':
    unittest.main()
