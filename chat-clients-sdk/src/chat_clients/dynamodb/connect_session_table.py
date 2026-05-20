"""ddb.py: Helper class that provides utilities for writing and accessing Amazon Connect Chat session data in DynamoDB"""

import os
from logging import Logger
from typing import Any, Dict, List, Optional
from boto3.dynamodb.types import TypeDeserializer, TypeSerializer
from chat_clients.common.logging_helper import get_logger
from chat_clients.common.session_helper import get_boto3_session, get_boto3_client_config
from chat_clients.common.time_helper import get_current_local_time, get_iso_timestamp

class ConnectSessionTable:
    """
    The ConnectSessionTable class implements helper functions that interact with the
    DynamoDB (DDB) table.  Table stores Amazon Connect chat metadata values that
    are used by Lambda function to send Amazon Connect replies back to the front
    end user properly.

    The table contains following attributes:

    - `id` (string) - hash key :
        - may contain user provided `session_id`
        - when operating with slack API, may contain 'user_id' from slack call
        - may also contain unique ids from third party apps besides slack
    - `contact_id` (string)            : Amazon Connect contact ID
    - `participant_id` (string)        : Amazon Connect participant ID
    - `participant_token` (string)     : Amazon Connect participant token
    - `streaming_id` (string)          : Amazon Connect streaming ID
    - `connection_token` (string)      : Amazon Connect Participant Service connection token
    - `payload` list(object)           : Payload sent from the front-end. This can be
                                         a list of events capturing user's conversation
    - `create_timestamp` (string)      : Timestamp when the item is created
    - `last_update_timestamp` (string) : Timestamp when the item is updated
    - `ttl` (number)                   : Time to live for the item. This is used to
                                         delete the item after the specified time.
                                         The default value is 1 day.
    - `agent_joined` (bool)            : True once a live agent has joined the chat.
                                         Set by connect-stream-lambda when it receives
                                         an AGENT-role SNS message. Used by
                                         connect-api-lambda to suppress the typing
                                         acknowledgement during live-agent conversations.

    """
    # class constants
    DEFAULT_TABLE_TTL: str = "3600" # 1 hour in seconds
    DEFAULT_GSI1_NAME: str = "contact_id-index"

    # class variables
    ddb_table_name: str = None
    ddb_table_ttl: int = 0
    ddb_client: Any = None
    deserializer: TypeDeserializer = None
    serializer: TypeSerializer = None
    logger: Logger = None

    logger: Logger = None
    def __init__(self) -> None:
        # configure logger
        self.logger = get_logger(f"{__name__}.{type(self).__name__}")

        # initialize env
        self.__init_env()

        # initialize ddb
        self.__init_ddb()

    def __init_env(self) -> None:
        """
        Read values from environment variables
        """
        # CONNECT_SESSION_DDB_TABLE_TTL
        self.ddb_table_ttl = int(os.environ.get("CONNECT_SESSION_DDB_TABLE_TTL", self.DEFAULT_TABLE_TTL))

        # if CONNECT_SESSION_DDB_TABLE_NAME environment variable is None or empty string, raise error
        self.ddb_table_name = os.environ.get("CONNECT_SESSION_DDB_TABLE_NAME", None)
        if not self.ddb_table_name or len(self.ddb_table_name) == 0:
            error_message = "CONNECT_SESSION_DDB_TABLE_NAME environment variable is not set"
            self.logger.error(error_message)
            raise ValueError(error_message)

    def __init_ddb(self) -> None:
        """
        Initialize DynamoDB client and Serializer/Deserializer
        """
        # configure boto3 session
        boto3_session = get_boto3_session()
        boto3_client_config = get_boto3_client_config()

        self.ddb_client = boto3_session.client("dynamodb")
        if boto3_client_config:
            self.ddb_client = boto3_session.client("dynamodb", config=boto3_client_config)

        # initialize serializer/deserializer
        self.deserializer = TypeDeserializer()
        self.serializer = TypeSerializer()

    def __get_item(self, hash_key: str) -> Dict[str, Any]:
        """
        Given a hash_key get exactly one item from DynamoDB (DDB) table using
        the DDB get_item API.  We must deserialize the DDB JSON into a
        normalized json before returning the result.  The resulting dictionary
        is in following format:

        {
            "id": "string",
            "contact_id": "string",
            "participant_id": "string",
            "participant_token": "string",
            "streaming_id": "string",
            "connection_token": "string",
            "payload": [
                {
                    "attribute1": "string",
                    "attribute2": "string",
                    "attribute3": {
                        "attribute4": "string",
                    },
                }
            ],
            "create_timestamp": "string",
            "last_update_timestamp": "string",
            "ttl": number
        }

        Args:
            hash_key (str): unique ID

        Returns:
            Dict: Data item retrieved from DDB.
        """
        table_keys = {
            'id': {'S': hash_key},
        }

        response = self.ddb_client.get_item(
            TableName=self.ddb_table_name,
            Key=table_keys
        )
        if 'Item' in response:
            self.logger.debug("Found item in DDB table: id='%s'", hash_key)
            return self.__deserialize_ddb_item(response['Item'])

        # raise error if item is not found
        error_message = f"Item not found in DDB table: id='{hash_key}'"
        self.logger.error(error_message)
        raise ValueError(error_message)

    def __query_item_with_gsi(self, hash_key: str) -> Dict[str, Any]:
        """
        Given a hash_key, get exactly one item from DynamoDB (DDB) table using
        the DDB query API.  We will query the table using DEFAULT_GSI1_NAME.
        There is only one item returned using the query method.

        We must deserialize the DDB JSON into a normalized json before returning
        the result.  Refer to `__get_item()` for response format.

        Args:
            hash_key (str): unique ID

        Returns:
            Dict: Data item retrieved from DDB.
        """
        # query table using DEFAULT_GSI1_NAME
        response = self.ddb_client.query(
            TableName=self.ddb_table_name,
            IndexName=self.DEFAULT_GSI1_NAME,
            KeyConditionExpression="contact_id = :contact_id",
            ExpressionAttributeValues={
                ":contact_id": {'S': hash_key}
            }
        )

        if 'Items' in response and len(response['Items']) > 0:
            self.logger.debug("Found item in DDB table: contact_id='%s'", hash_key)
            return self.__deserialize_ddb_item(response['Items'][0])

        # raise error if item is not found
        error_message = f"Item not found in DDB table: contact_id='{hash_key}'"
        self.logger.error(error_message)
        raise ValueError(error_message)

    def __deserialize_ddb_item(self, ddb_item: Dict[str, Any]) -> Dict[str, Any]:
        """
        Deserialize a DynamoDB item into a normalized json / dictionary.

        Args:
            ddb_item (Dict): DynamoDB item to be deserialized

        Returns:
            Dict: Normalized json
        """
        # initialize a new dictionary to hold deserialized values
        deserialized_item = {}
        for k, v in ddb_item.items():
            deserialized_item[k] = self.deserializer.deserialize(v)

        return deserialized_item

    def __put_item(self, item: Dict[str, Any]) -> None:
        """
        Put an item into DynamoDB (DDB) table.  `item` must be in following
        format:
        {
            "id": "string",
            "contact_id": "string",
            "participant_id": "string",
            "participant_token": "string",
            "streaming_id": "string",
            "connection_token": "string",
            "payload": [
                {
                    "attribute1": "string",
                    "attribute2": "string",
                    "attribute3": {
                        "attribute4": "string",
                    },
                }
            ],
            "create_timestamp": "string",
            "last_update_timestamp": "string",
            "ttl": number
        }

        Args:
            item (Dict): item to be put into DDB
        """
        # get time in ISO 8601 format with local timezone
        current_ts = get_current_local_time()
        iso_ts_str = get_iso_timestamp(current_ts)

        # whenever we touch the item (put/update), we need to update the ttl
        # calculate ttl value as current_ts (in unix epoch) + self.ddb_table_ttl
        ttl = int(current_ts.timestamp()) + self.ddb_table_ttl

        # id and contact_id are required; throw error if they are empty
        _id = item.get("id", None)
        contact_id = item.get("contact_id", None)
        if not _id:
            error_message = "id cannot be empty"
            self.logger.error(error_message)
            raise ValueError(error_message)
        if not contact_id:
            error_message = "contact_id cannot be empty"
            self.logger.error(error_message)
            raise ValueError(error_message)

        # compute create_timestamp if it is not provided in the item
        if not item.get("create_timestamp"):
            item["create_timestamp"] = iso_ts_str

        # always override last_update_timestamp with current time
        item["last_update_timestamp"] = iso_ts_str

        # check all remaining attributes.  If they are empty, set them to None
        if not item.get("participant_id"):
            item["participant_id"] = None
        if not item.get("participant_token"):
            item["participant_token"] = None
        if not item.get("streaming_id"):
            item["streaming_id"] = None
        if not item.get("connection_token"):
            item["connection_token"] = None
        if not item.get("payload"):
            item["payload"] = None

        ddb_item = {
            # required attributes
            "id": self.serializer.serialize(_id),
            "contact_id": self.serializer.serialize(contact_id),
            # optional attributes
            "participant_id":
                self.serializer.serialize(item.get("participant_id")) if item.get("participant_id") else None,
            "participant_token":
                self.serializer.serialize(item.get("participant_token")) if item.get("participant_token") else None,
            "streaming_id":
                self.serializer.serialize(item.get("streaming_id")) if item.get("streaming_id") else None,
            "connection_token":
                self.serializer.serialize(item.get("connection_token")) if item.get("connection_token") else None,
            "payload":
                self.serializer.serialize(item["payload"]) if item.get("payload") else None,
            "agent_joined":
                self.serializer.serialize(item.get("agent_joined", False)),
            # required attributes
            "create_timestamp": self.serializer.serialize(item.get("create_timestamp")),
            "last_update_timestamp": self.serializer.serialize(item.get("last_update_timestamp")),
            "ttl": self.serializer.serialize(ttl)
        }

        # clean None values from ddb_item
        ddb_item = {k: v for k, v in ddb_item.items() if v is not None}

        self.ddb_client.put_item(
            TableName=self.ddb_table_name,
            Item=ddb_item
        )
        self.logger.debug("Successfully wrote item to DDB table: id='%s', contact_id='%s'", _id, contact_id)

    def __delete_item(self, key: str) -> None:
        """
        Delete an item from DynamoDB (DDB) table.

        Args:
            key (str): unique ID
        """
        table_keys = {
            'id': {'S': key},
        }

        self.ddb_client.delete_item(
            TableName=self.ddb_table_name,
            Key=table_keys
        )
        self.logger.debug("Successfully deleted item from DDB table: id='%s'", key)

    def get_item_by_id(self, key: str) -> Dict:
        """
        Get Amazon Connect chat session for a given hash_key.

        Args:
            key (str) (required): hash key is typically set to the `session_id` or `user_id`

        Returns:
            Dict: Returns the response from DDB
        """
        return self.__get_item(key)

    def get_item_by_contact_id(self, key: str) -> Dict:
        """
        Get Amazon Connect chat session using `contact_id`

        Args:
            key (str) (required): `contact_id`

        Returns:
            Dict: Returns the response from DDB
        """
        return self.__query_item_with_gsi(key)

    def add_item(self,
        key: str,
        contact_id: str,
        participant_id: str,
        participant_token: str,
        connection_token: str,
        payload: List[Dict[str, Any]],
        streaming_id: Optional[str] = None,
    ) -> None:
        """
        Add Amazon Connect chat session to DDB.

        Args:
            key (str) (required): hash key is typically set to the `session_id` or `user_id`
            contact_id (str) (required): `contact_id`
            participant_id (str) (required): `participant_id`
            participant_token (str) (required): `participant_token`
            streaming_id (str) (required): `streaming_id`
            payload (List[Dict[str, Any]]) (required): `payload`
            connection_token (str) (optional): `connection_token`
        """
        # create a new dictionary to hold the item to be written
        item = {
            "id": key,
            "contact_id": contact_id,
            "participant_id": participant_id,
            "participant_token": participant_token,
            "streaming_id": streaming_id,
            "connection_token": connection_token,
            "payload": payload,
        }
        self.__put_item(item)

    def update_item(
        self, key: str,
        contact_id: Optional[str] = None,
        participant_id: Optional[str] = None,
        participant_token: Optional[str] = None,
        streaming_id: Optional[str] = None,
        connection_token: Optional[str] = None,
        payload: Optional[List[Dict[str, Any]]] = None) -> None:
        """
        Update an existing item in DDB.

        Args:
            key (str) (required): hash key is typically set to the `session_id` or `user_id`
            contact_id (str) (optional): `contact_id`
            participant_id (str) (optional): `participant_id`
            participant_token (str) (optional): `participant_token`
            streaming_id (str) (optional): `streaming_id`
            connection_token (str) (optional): `connection_token`
            payload (List[Dict[str, Any]]) (optional): `payload`
        """
        # get existing item from DDB
        item = self.__get_item(key)

        # update the item with the new values
        if contact_id:
            item["contact_id"] = contact_id
        if participant_id:
            item["participant_id"] = participant_id
        if participant_token:
            item["participant_token"] = participant_token
        if streaming_id:
            item["streaming_id"] = streaming_id
        if connection_token:
            item["connection_token"] = connection_token
        if payload:
            item["payload"] = payload

        self.__put_item(item)

    def set_agent_joined(self, key: str) -> None:
        """
        Atomically set agent_joined=True on an existing session item.
        Uses a targeted UpdateItem expression to avoid a read-modify-write
        race condition with connect-api-lambda.

        Args:
            key (str): hash key (user_id)
        """
        current_ts = get_current_local_time()
        iso_ts_str = get_iso_timestamp(current_ts)

        self.ddb_client.update_item(
            TableName=self.ddb_table_name,
            Key={"id": {"S": key}},
            UpdateExpression="SET agent_joined = :val, last_update_timestamp = :ts",
            ExpressionAttributeValues={
                ":val": {"BOOL": True},
                ":ts":  {"S": iso_ts_str},
            }
        )
        self.logger.debug("Set agent_joined=True for id='%s'", key)

    def delete_item(self, key: str) -> None:
        """
        Delete an item from DynamoDB (DDB) table.

        Args:
            key (str): unique ID
        """
        self.__delete_item(key)
