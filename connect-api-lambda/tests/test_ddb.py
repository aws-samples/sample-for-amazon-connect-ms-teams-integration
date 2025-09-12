# pylint: disable=import-error,unused-import
# hack to make sure we can import modules in ../src/** modules
try:
    import __setup__
except ModuleNotFoundError:
    import tests.__setup__
# end hack
# pylint: enable=import-error,unused-import

import os
import unittest
from chat_clients.dynamodb.connect_session_table import ConnectSessionTable

class TestConnectSessionTable(unittest.TestCase):
    """TestConnectSessionTable"""
    def __init__(self, *args, **kwargs):
        super(TestConnectSessionTable, self).__init__(*args, **kwargs)

    def setUp(self):
        super().setUp()

        # set env
        os.environ["CONNECT_SESSION_DDB_TABLE_NAME"] = "connect-session-table"
        os.environ["CONNECT_SESSION_DDB_TABLE_TTL"] = "3600"

    def test_connect_session_table(self):
        """test_connect_session_table"""
        # sample data
        _id = "test-id"
        contact_id = "f439b5c7-3537-4bb3-b4c6-90185fa28c9b"
        participant_id = "test-participant-id"
        participant_token = "test-participant-token"
        streaming_id = "test-streaming-id"
        payload = [
            {
                "attribute1": "value1",
                "attribute2": "value2",
                "attribute3": {
                    "attribute4": "value4"
                }
            }
        ]

        # instantiate the class - table must already exist
        table = ConnectSessionTable()

        # add some data in table
        table.add_item(_id, contact_id, participant_id, participant_token, streaming_id, payload)

        # get data from table
        item = table.get_item_by_id(_id)
        self.assertEqual(item["id"], _id)

        # get data from table using GSI
        item = table.get_item_by_contact_id(contact_id)
        self.assertEqual(item["id"], _id)
        self.assertEqual(item["contact_id"], contact_id)

        # update data in table
        payload2 = [
            {
                "attribute1": "value1",
                "attribute2": "value2"
            }
        ]
        table.update_item(_id, payload=payload2)
        item = table.get_item_by_id(_id)
        self.assertEqual(item["id"], _id)
        self.assertEqual(item["payload"], payload2)
        self.assertNotEqual(item["create_timestamp"], item["last_update_timestamp"])

        # delete data in table
        table.delete_item(_id)
        self.assertRaises(Exception, table.get_item_by_id, _id)
        self.assertRaises(Exception, table.get_item_by_contact_id, contact_id)

