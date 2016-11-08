import unittest
from unittest.mock import MagicMock
from pagure_importer.utils.importer_trac import (TracImporter, to_timestamp)


class PgimportImporterTrac (unittest.TestCase):

    def setUp(self):
        self.trac = TracImporter(project_url="https://foobar.bar",
                                 username="foo",
                                 password="bar",
                                 offset=0,
                                 repo_folder="myfolder",
                                 repo_name="myname",
                                 nopush=False)
        self.somebody = {'name': 'somebody', 'fullname': 'somebody',
                         'emails': ['some@body.com']}

        self.mock_request = MagicMock()
        self.old_request = TracImporter.request
        TracImporter.request = self.mock_request

    def tearDown(self):
        TracImporter.request = self.old_request

    def test_import_2_comments(self):

        # Case 1 - Import 2 comments
        trac_comments = [
            [{u'__jsonclass__': [u'datetime', u'2016-11-08T20:30:13']}, u'foobar',
             u'comment', u'1', u'Yeah, let\'s have some test.', 1],
            [{u'__jsonclass__': [u'datetime', u'2016-11-08T20:32:20']}, u'foobar',
             u'comment', u'2', u'Well this will improve the code base :).', 1]]

        results = TracImporter.create_comments(self.trac, trac_comments)

        ts_1 = to_timestamp(trac_comments[0][0]['__jsonclass__'][1])

        self.assertEqual("Yeah, let\'s have some test.",
                         results[ts_1].comment)
        self.assertEqual(ts_1, results[ts_1].date_created)
        self.assertEqual([], results[ts_1].attachment)
        self.assertEqual(self.somebody, results[ts_1].user)

        ts_2 = to_timestamp(trac_comments[1][0]['__jsonclass__'][1])

        self.assertEqual("Well this will improve the code base :).",
                         results[ts_2].comment)
        self.assertEqual(ts_2, results[ts_2].date_created)
        self.assertEqual([], results[ts_2].attachment)
        self.assertEqual(self.somebody, results[ts_2].user)

    def test_import_empty_comments(self):
        # Case 2 - Import an empty comment, returns and empty dic.
        trac_comments = [
            [{u'__jsonclass__': [u'datetime', u'2016-11-08T20:30:13']}, u'foobar',
             u'comment', u'1', u'', 1]]

        results = TracImporter.create_comments(self.trac, trac_comments)
        self.assertEqual({}, results)

    def test_import_not_a_comments(self):
        # Case 3 - Import something which is not a comment, returns an empty dic.
        trac_comments = [
            [{u'__jsonclass__': [u'datetime', u'2014-04-09T16:02:20']}, u'foobar',
             u'resolution', u'', u'wontfix', 1]]

        results = TracImporter.create_comments(self.trac, trac_comments)
        self.assertEqual({}, results)

    def test_import_attachment(self):
        # Case 4 - Import an attachment
        trac_comments = [
            [{u'__jsonclass__': [u'datetime', u'2014-10-31T12:32:18']}, u'foobar',
             u'attachment', u'', u'mytest.png', 0]]

        results = TracImporter.create_comments(self.trac, trac_comments)
        ts_1 = to_timestamp(trac_comments[0][0]['__jsonclass__'][1])

        self.assertEqual("attachment",
                         results[ts_1].comment)
        self.assertEqual(ts_1, results[ts_1].date_created)
        self.assertEqual(['mytest.png'], results[ts_1].attachment)
        self.assertEqual(self.somebody, results[ts_1].user)

    def test_import_attachment_and_comment(self):
        # Case 5 - Import an Attachment then a Comment (same timestamp)
        trac_comments = [
            [{u'__jsonclass__': [u'datetime', u'2014-10-31T12:32:18']}, u'foobar',
             u'attachment', u'', u'mytest.png', 0],
            [{u'__jsonclass__': [u'datetime', u'2014-10-31T12:32:18']}, u'foobar',
             u'comment', u'', u'test attachment', 0]]

        results = TracImporter.create_comments(self.trac, trac_comments)
        ts_1 = to_timestamp(trac_comments[0][0]['__jsonclass__'][1])

        self.assertEqual("test attachment",
                         results[ts_1].comment)
        self.assertEqual(ts_1, results[ts_1].date_created)
        self.assertEqual(['mytest.png'], results[ts_1].attachment)
        self.assertEqual(self.somebody, results[ts_1].user)

    def test_import_comment_and_attachment(self):
        # Case 6 - Import a Comment then an Attachment (same timestamp)
        trac_comments = [
            [{u'__jsonclass__': [u'datetime', u'2014-10-31T12:32:18']}, u'foobar',
             u'comment', u'', u'test attachment', 0],
            [{u'__jsonclass__': [u'datetime', u'2014-10-31T12:32:18']}, u'foobar',
             u'attachment', u'', u'mytest.png', 0]]

        results = TracImporter.create_comments(self.trac, trac_comments)
        ts_1 = to_timestamp(trac_comments[0][0]['__jsonclass__'][1])

        self.assertEqual("test attachment",
                         results[ts_1].comment)
        self.assertEqual(ts_1, results[ts_1].date_created)
        self.assertEqual(['mytest.png'], results[ts_1].attachment)
        self.assertEqual(self.somebody, results[ts_1].user)

    def test_import_2attachment_and_comment(self):
        # Case 7 - Import 2 Attachments then a Comment (same timestamp)
        trac_comments = [
            [{u'__jsonclass__': [u'datetime', u'2014-10-31T12:32:18']}, u'foobar',
             u'attachment', u'', u'mytest.png', 0],
            [{u'__jsonclass__': [u'datetime', u'2014-10-31T12:32:18']}, u'foobar',
             u'attachment', u'', u'mysecondtest.png', 0],
            [{u'__jsonclass__': [u'datetime', u'2014-10-31T12:32:18']}, u'foobar',
             u'comment', u'', u'test 2 attachments', 0]]

        results = TracImporter.create_comments(self.trac, trac_comments)
        ts_1 = to_timestamp(trac_comments[0][0]['__jsonclass__'][1])

        self.assertEqual("test 2 attachments",
                         results[ts_1].comment)
        self.assertEqual(ts_1, results[ts_1].date_created)
        self.assertEqual(['mytest.png', 'mysecondtest.png'], results[ts_1].attachment)
        self.assertEqual(self.somebody, results[ts_1].user)

    def test_get_ticket_status_open(self):

        trac_ticket = {'status': 'open'}

        results = TracImporter.get_ticket_status(self.trac, trac_ticket)
        self.assertEqual(('Open', ''), results)

    def test_get_ticket_status_closedInvalid(self):

        trac_ticket = {'status': 'closed', 'resolution': 'invalid'}

        results = TracImporter.get_ticket_status(self.trac, trac_ticket)
        self.assertEqual(('Closed', 'Invalid'), results)

    def test_get_ticket_status_closedWontFix(self):
        trac_ticket = {'status': 'closed', 'resolution': 'wontfix'}

        results = TracImporter.get_ticket_status(self.trac, trac_ticket)
        self.assertEqual(('Closed', 'Invalid'), results)

    def test_get_ticket_status_closedWorksforme(self):
        trac_ticket = {'status': 'closed', 'resolution': 'worksforme'}

        results = TracImporter.get_ticket_status(self.trac, trac_ticket)
        self.assertEqual(('Closed', 'Invalid'), results)

    def test_get_ticket_status_closedDuplicate(self):
        trac_ticket = {'status': 'closed', 'resolution': 'duplicate'}

        results = TracImporter.get_ticket_status(self.trac, trac_ticket)
        self.assertEqual(('Closed', 'Duplicate'), results)

    def test_get_ticket_status_closedInsufficient(self):
        trac_ticket = {'status': 'closed', 'resolution': 'insufficient_info'}

        results = TracImporter.get_ticket_status(self.trac, trac_ticket)
        self.assertEqual(('Closed', 'Insufficient data'), results)

    def test_get_ticket_status_closedFixed(self):
        trac_ticket = {'status': 'closed', 'resolution': 'fixed'}

        results = TracImporter.get_ticket_status(self.trac, trac_ticket)
        self.assertEqual(('Closed', 'Fixed'), results)

    def test_get_custom_fieldsText(self):
        self.mock_request.return_value = [{'custom': True, 'name': 'foo', 'type': 'textarea'}]
        results = TracImporter.get_custom_fields(self.trac)
        self.assertEqual([{'key_type': 'text', 'name': 'foo'}], results)

    def test_get_custom_fieldsBoolean(self):
        self.mock_request.return_value = [{'custom': True, 'name': 'bar', 'type': 'checkbox'}]
        results = TracImporter.get_custom_fields(self.trac)
        self.assertEqual([{'key_type': 'boolean', 'name': 'bar'}], results)

    def test_get_tickets_custom_fiedls(self):
        self.trac.custom_fields = [{'key_type': 'text', 'name': 'bar'},
                                   {'key_type': 'boolean', 'name': 'foo'}]
        trac_ticket = {'bar': 'hello', 'foo': 'world', 'foobar': 'hello world'}
        results = TracImporter.get_custom_fields_of_ticket(self.trac, trac_ticket)
        self.assertDictEqual({'key_type': 'text', 'value': 'hello', 'name': 'bar'}, results[0])
        self.assertDictEqual({'key_type': 'boolean', 'value': 'world', 'name': 'foo'}, results[1])
