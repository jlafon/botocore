# Copyright 2012-2014 Amazon.com, Inc. or its affiliates. All Rights Reserved.
#
# Licensed under the Apache License, Version 2.0 (the "License"). You
# may not use this file except in compliance with the License. A copy of
# the License is located at
#
# http://aws.amazon.com/apache2.0/
#
# or in the "license" file accompanying this file. This file is
# distributed on an "AS IS" BASIS, WITHOUT WARRANTIES OR CONDITIONS OF
# ANY KIND, either express or implied. See the License for the specific
# language governing permissions and limitations under the License.

from tests import unittest
import botocore.session
from botocore.hooks import first_non_none_response
from botocore.compat import quote
import base64
import six

import mock


class TestHandlers(unittest.TestCase):

    def setUp(self):
        self.session = botocore.session.get_session()

    def tearDown(self):
        pass

    def test_get_console_output(self):
        event = self.session.create_event('after-parsed', 'ec2',
                                          'GetConsoleOutput',
                                          'String', 'Output')
        value = base64.b64encode(six.b('foobar')).decode('utf-8')
        rv = self.session.emit(event, shape={}, value=value)
        converted_value = first_non_none_response(rv)
        self.assertEqual(converted_value, 'foobar')

    def test_decode_quoted_jsondoc(self):
        event = self.session.create_event('after-parsed', 'iam',
                                          'GetUserPolicy',
                                          'policyDocumentType',
                                          'PolicyDocument')
        value = quote('{"foo":"bar"}')
        rv = self.session.emit(event, shape={}, value=value)
        converted_value = first_non_none_response(rv)
        self.assertEqual(converted_value, {'foo': 'bar'})

    def test_decode_jsondoc(self):
        event = self.session.create_event('after-parsed', 'cloudformation',
                                          'GetTemplate',
                                          'TemplateBody',
                                          'TemplateBody')
        value = '{"foo":"bar"}'
        rv = self.session.emit(event, shape={}, value=value)
        converted_value = first_non_none_response(rv)
        self.assertEqual(converted_value, {'foo':'bar'})

    def test_switch_to_sigv4(self):
        event = self.session.create_event('service-data-loaded', 's3')
        mock_session = mock.Mock()
        mock_session.get_config.return_value = {
            's3': {'signature_version': 's3v4'},
        }
        kwargs = {'service_data': {'signature_version': 's3'},
                  'service_name': 's3', 'session': mock_session}
        self.session.emit(event, **kwargs)
        self.assertEqual(kwargs['service_data']['signature_version'], 's3v4')

    def test_noswitch_to_sigv4(self):
        event = self.session.create_event('service-data-loaded', 's3')
        mock_session = mock.Mock()
        mock_session.get_config.return_value = {}
        kwargs = {'service_data': {'signature_version': 's3'},
                  'service_name': 's3', 'session': mock_session}
        self.session.emit(event, **kwargs)
        self.assertEqual(kwargs['service_data']['signature_version'], 's3')


if __name__ == '__main__':
    unittest.main()
