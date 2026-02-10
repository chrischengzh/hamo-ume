"""
DynamoDB Database Module for Hamo-UME
Handles all database operations for conversation-related entities
"""

import boto3
from boto3.dynamodb.conditions import Key, Attr
from typing import Optional, Dict, List, Any
from datetime import datetime
import json
import os
from decimal import Decimal

# ============================================================
# DYNAMODB CONFIGURATION
# ============================================================

# Get AWS configuration from environment variables
AWS_REGION = os.getenv("AWS_REGION", "us-east-1")
AWS_ACCESS_KEY_ID = os.getenv("AWS_ACCESS_KEY_ID", None)
AWS_SECRET_ACCESS_KEY = os.getenv("AWS_SECRET_ACCESS_KEY", None)

# For local development, you can use DynamoDB Local
DYNAMODB_ENDPOINT = os.getenv("DYNAMODB_ENDPOINT", None)  # e.g., http://localhost:8000

# Initialize DynamoDB client
if DYNAMODB_ENDPOINT:
    # Local development
    dynamodb = boto3.resource(
        'dynamodb',
        endpoint_url=DYNAMODB_ENDPOINT,
        region_name=AWS_REGION,
        aws_access_key_id='dummy',
        aws_secret_access_key='dummy'
    )
elif AWS_ACCESS_KEY_ID and AWS_SECRET_ACCESS_KEY:
    # AWS with explicit credentials
    dynamodb = boto3.resource(
        'dynamodb',
        region_name=AWS_REGION,
        aws_access_key_id=AWS_ACCESS_KEY_ID,
        aws_secret_access_key=AWS_SECRET_ACCESS_KEY
    )
else:
    # AWS with IAM role (Elastic Beanstalk)
    dynamodb = boto3.resource('dynamodb', region_name=AWS_REGION)

# ============================================================
# TABLE NAMES
# ============================================================

TABLE_USERS = "hamo_users"
TABLE_AVATARS = "hamo_avatars"
TABLE_AI_MINDS = "hamo_ai_minds"
TABLE_PSVS_PROFILES = "hamo_psvs_profiles"
TABLE_SESSIONS = "hamo_conversation_sessions"
TABLE_MESSAGES = "hamo_conversation_messages"
TABLE_CONNECTIONS = "hamo_client_avatar_connections"
TABLE_INVITATIONS = "hamo_invitations"
TABLE_REFRESH_TOKENS = "hamo_refresh_tokens"

# ============================================================
# HELPER FUNCTIONS
# ============================================================

def serialize_for_dynamodb(data: Any) -> Any:
    """
    Convert Python objects to DynamoDB-compatible format
    - Converts floats to Decimal
    - Converts datetime to ISO string
    - Handles nested objects
    """
    if isinstance(data, dict):
        return {k: serialize_for_dynamodb(v) for k, v in data.items()}
    elif isinstance(data, list):
        return [serialize_for_dynamodb(item) for item in data]
    elif isinstance(data, float):
        return Decimal(str(data))
    elif isinstance(data, datetime):
        return data.isoformat()
    else:
        return data

def deserialize_from_dynamodb(data: Any) -> Any:
    """
    Convert DynamoDB format back to Python objects
    - Converts Decimal to float
    - Keeps ISO strings as strings (FastAPI will parse them)
    """
    if isinstance(data, dict):
        return {k: deserialize_from_dynamodb(v) for k, v in data.items()}
    elif isinstance(data, list):
        return [deserialize_from_dynamodb(item) for item in data]
    elif isinstance(data, Decimal):
        return float(data)
    else:
        return data

# ============================================================
# TABLE INITIALIZATION
# ============================================================

def create_tables():
    """
    Create all required DynamoDB tables
    Only needs to be run once during initial setup
    """
    tables_config = [
        {
            "TableName": TABLE_USERS,
            "KeySchema": [{"AttributeName": "id", "KeyType": "HASH"}],
            "AttributeDefinitions": [
                {"AttributeName": "id", "AttributeType": "S"},
                {"AttributeName": "email", "AttributeType": "S"}
            ],
            "GlobalSecondaryIndexes": [{
                "IndexName": "email-index",
                "KeySchema": [{"AttributeName": "email", "KeyType": "HASH"}],
                "Projection": {"ProjectionType": "ALL"},
                "ProvisionedThroughput": {"ReadCapacityUnits": 5, "WriteCapacityUnits": 5}
            }],
            "ProvisionedThroughput": {"ReadCapacityUnits": 5, "WriteCapacityUnits": 5}
        },
        {
            "TableName": TABLE_AVATARS,
            "KeySchema": [{"AttributeName": "id", "KeyType": "HASH"}],
            "AttributeDefinitions": [
                {"AttributeName": "id", "AttributeType": "S"},
                {"AttributeName": "pro_user_id", "AttributeType": "S"}
            ],
            "GlobalSecondaryIndexes": [{
                "IndexName": "pro_user_id-index",
                "KeySchema": [{"AttributeName": "pro_user_id", "KeyType": "HASH"}],
                "Projection": {"ProjectionType": "ALL"},
                "ProvisionedThroughput": {"ReadCapacityUnits": 5, "WriteCapacityUnits": 5}
            }],
            "ProvisionedThroughput": {"ReadCapacityUnits": 5, "WriteCapacityUnits": 5}
        },
        {
            "TableName": TABLE_AI_MINDS,
            "KeySchema": [{"AttributeName": "id", "KeyType": "HASH"}],
            "AttributeDefinitions": [
                {"AttributeName": "id", "AttributeType": "S"},
                {"AttributeName": "user_id", "AttributeType": "S"},
                {"AttributeName": "avatar_id", "AttributeType": "S"}
            ],
            "GlobalSecondaryIndexes": [
                {
                    "IndexName": "user_id-index",
                    "KeySchema": [{"AttributeName": "user_id", "KeyType": "HASH"}],
                    "Projection": {"ProjectionType": "ALL"},
                    "ProvisionedThroughput": {"ReadCapacityUnits": 5, "WriteCapacityUnits": 5}
                },
                {
                    "IndexName": "avatar_id-index",
                    "KeySchema": [{"AttributeName": "avatar_id", "KeyType": "HASH"}],
                    "Projection": {"ProjectionType": "ALL"},
                    "ProvisionedThroughput": {"ReadCapacityUnits": 5, "WriteCapacityUnits": 5}
                }
            ],
            "ProvisionedThroughput": {"ReadCapacityUnits": 5, "WriteCapacityUnits": 5}
        },
        {
            "TableName": TABLE_PSVS_PROFILES,
            "KeySchema": [{"AttributeName": "mind_id", "KeyType": "HASH"}],
            "AttributeDefinitions": [
                {"AttributeName": "mind_id", "AttributeType": "S"}
            ],
            "ProvisionedThroughput": {"ReadCapacityUnits": 5, "WriteCapacityUnits": 5}
        },
        {
            "TableName": TABLE_SESSIONS,
            "KeySchema": [{"AttributeName": "id", "KeyType": "HASH"}],
            "AttributeDefinitions": [
                {"AttributeName": "id", "AttributeType": "S"},
                {"AttributeName": "user_id", "AttributeType": "S"},
                {"AttributeName": "mind_id", "AttributeType": "S"}
            ],
            "GlobalSecondaryIndexes": [
                {
                    "IndexName": "user_id-index",
                    "KeySchema": [{"AttributeName": "user_id", "KeyType": "HASH"}],
                    "Projection": {"ProjectionType": "ALL"},
                    "ProvisionedThroughput": {"ReadCapacityUnits": 5, "WriteCapacityUnits": 5}
                },
                {
                    "IndexName": "mind_id-index",
                    "KeySchema": [{"AttributeName": "mind_id", "KeyType": "HASH"}],
                    "Projection": {"ProjectionType": "ALL"},
                    "ProvisionedThroughput": {"ReadCapacityUnits": 5, "WriteCapacityUnits": 5}
                }
            ],
            "ProvisionedThroughput": {"ReadCapacityUnits": 5, "WriteCapacityUnits": 5}
        },
        {
            "TableName": TABLE_MESSAGES,
            "KeySchema": [{"AttributeName": "id", "KeyType": "HASH"}],
            "AttributeDefinitions": [
                {"AttributeName": "id", "AttributeType": "S"},
                {"AttributeName": "session_id", "AttributeType": "S"}
            ],
            "GlobalSecondaryIndexes": [{
                "IndexName": "session_id-index",
                "KeySchema": [{"AttributeName": "session_id", "KeyType": "HASH"}],
                "Projection": {"ProjectionType": "ALL"},
                "ProvisionedThroughput": {"ReadCapacityUnits": 5, "WriteCapacityUnits": 5}
            }],
            "ProvisionedThroughput": {"ReadCapacityUnits": 5, "WriteCapacityUnits": 5}
        },
        {
            "TableName": TABLE_CONNECTIONS,
            "KeySchema": [{"AttributeName": "id", "KeyType": "HASH"}],
            "AttributeDefinitions": [
                {"AttributeName": "id", "AttributeType": "S"},
                {"AttributeName": "client_user_id", "AttributeType": "S"},
                {"AttributeName": "avatar_id", "AttributeType": "S"}
            ],
            "GlobalSecondaryIndexes": [
                {
                    "IndexName": "client_user_id-index",
                    "KeySchema": [{"AttributeName": "client_user_id", "KeyType": "HASH"}],
                    "Projection": {"ProjectionType": "ALL"},
                    "ProvisionedThroughput": {"ReadCapacityUnits": 5, "WriteCapacityUnits": 5}
                },
                {
                    "IndexName": "avatar_id-index",
                    "KeySchema": [{"AttributeName": "avatar_id", "KeyType": "HASH"}],
                    "Projection": {"ProjectionType": "ALL"},
                    "ProvisionedThroughput": {"ReadCapacityUnits": 5, "WriteCapacityUnits": 5}
                }
            ],
            "ProvisionedThroughput": {"ReadCapacityUnits": 5, "WriteCapacityUnits": 5}
        },
        {
            "TableName": TABLE_INVITATIONS,
            "KeySchema": [{"AttributeName": "code", "KeyType": "HASH"}],
            "AttributeDefinitions": [
                {"AttributeName": "code", "AttributeType": "S"},
                {"AttributeName": "pro_user_id", "AttributeType": "S"}
            ],
            "GlobalSecondaryIndexes": [{
                "IndexName": "pro_user_id-index",
                "KeySchema": [{"AttributeName": "pro_user_id", "KeyType": "HASH"}],
                "Projection": {"ProjectionType": "ALL"},
                "ProvisionedThroughput": {"ReadCapacityUnits": 5, "WriteCapacityUnits": 5}
            }],
            "ProvisionedThroughput": {"ReadCapacityUnits": 5, "WriteCapacityUnits": 5}
        },
        {
            "TableName": TABLE_REFRESH_TOKENS,
            "KeySchema": [{"AttributeName": "token", "KeyType": "HASH"}],
            "AttributeDefinitions": [
                {"AttributeName": "token", "AttributeType": "S"}
            ],
            "ProvisionedThroughput": {"ReadCapacityUnits": 5, "WriteCapacityUnits": 5}
        }
    ]

    existing_tables = [table.name for table in dynamodb.tables.all()]

    for config in tables_config:
        table_name = config["TableName"]
        if table_name not in existing_tables:
            print(f"Creating table: {table_name}")
            try:
                dynamodb.create_table(**config)
                print(f"✓ Table {table_name} created successfully")
            except Exception as e:
                print(f"✗ Error creating table {table_name}: {e}")
        else:
            print(f"○ Table {table_name} already exists")

# ============================================================
# CRUD OPERATIONS
# ============================================================

class DynamoDBManager:
    """Handles all DynamoDB operations"""

    def __init__(self):
        self.users = dynamodb.Table(TABLE_USERS)
        self.avatars = dynamodb.Table(TABLE_AVATARS)
        self.ai_minds = dynamodb.Table(TABLE_AI_MINDS)
        self.psvs_profiles = dynamodb.Table(TABLE_PSVS_PROFILES)
        self.sessions = dynamodb.Table(TABLE_SESSIONS)
        self.messages = dynamodb.Table(TABLE_MESSAGES)
        self.connections = dynamodb.Table(TABLE_CONNECTIONS)
        self.invitations = dynamodb.Table(TABLE_INVITATIONS)
        self.refresh_tokens = dynamodb.Table(TABLE_REFRESH_TOKENS)

    # ========== GENERIC OPERATIONS ==========

    def put_item(self, table_name: str, item: Dict) -> Dict:
        """Put an item into a table"""
        table = getattr(self, table_name.replace(f"hamo_", "").replace("conversation_", ""))
        serialized_item = serialize_for_dynamodb(item)
        table.put_item(Item=serialized_item)
        return item

    def get_item(self, table_name: str, key: Dict) -> Optional[Dict]:
        """Get an item from a table"""
        table = getattr(self, table_name.replace(f"hamo_", "").replace("conversation_", ""))
        response = table.get_item(Key=key)
        if 'Item' in response:
            return deserialize_from_dynamodb(response['Item'])
        return None

    def delete_item(self, table_name: str, key: Dict):
        """Delete an item from a table"""
        table = getattr(self, table_name.replace(f"hamo_", "").replace("conversation_", ""))
        table.delete_item(Key=key)

    def query_by_index(self, table_name: str, index_name: str, key_name: str, key_value: str) -> List[Dict]:
        """Query items using a Global Secondary Index"""
        table = getattr(self, table_name.replace(f"hamo_", "").replace("conversation_", ""))
        response = table.query(
            IndexName=index_name,
            KeyConditionExpression=Key(key_name).eq(key_value)
        )
        return [deserialize_from_dynamodb(item) for item in response.get('Items', [])]

    def scan_table(self, table_name: str, filter_expression=None) -> List[Dict]:
        """Scan entire table (use sparingly in production)"""
        table = getattr(self, table_name.replace(f"hamo_", "").replace("conversation_", ""))
        if filter_expression:
            response = table.scan(FilterExpression=filter_expression)
        else:
            response = table.scan()
        return [deserialize_from_dynamodb(item) for item in response.get('Items', [])]

    # ========== USERS ==========

    def create_user(self, user_data: Dict) -> Dict:
        """Create a new user"""
        return self.put_item("users", user_data)

    def get_user_by_id(self, user_id: str) -> Optional[Dict]:
        """Get user by ID"""
        return self.get_item("users", {"id": user_id})

    def get_user_by_email(self, email: str) -> Optional[Dict]:
        """Get user by email"""
        results = self.query_by_index("users", "email-index", "email", email)
        return results[0] if results else None

    def get_all_users(self) -> List[Dict]:
        """Get all users (for portal/stats)"""
        return self.scan_table("users")

    # ========== AVATARS ==========

    def create_avatar(self, avatar_data: Dict) -> Dict:
        """Create a new avatar
        Maps therapist_id → pro_user_id for database storage
        """
        data = avatar_data.copy()
        if "therapist_id" in data:
            data["pro_user_id"] = data.pop("therapist_id")
        return self.put_item("avatars", data)

    def get_avatar_by_id(self, avatar_id: str) -> Optional[Dict]:
        """Get avatar by ID
        Maps pro_user_id → therapist_id for application use
        """
        result = self.get_item("avatars", {"id": avatar_id})
        if result and "pro_user_id" in result:
            result["therapist_id"] = result.pop("pro_user_id")
        return result

    def get_avatars_by_pro(self, pro_user_id: str) -> List[Dict]:
        """Get all avatars for a therapist
        Maps pro_user_id → therapist_id for application use
        """
        results = self.query_by_index("avatars", "pro_user_id-index", "pro_user_id", pro_user_id)
        for result in results:
            if "pro_user_id" in result:
                result["therapist_id"] = result.pop("pro_user_id")
        return results

    def get_all_avatars(self) -> List[Dict]:
        """Get all avatars (for discover page)
        Maps pro_user_id → therapist_id for application use
        """
        results = self.scan_table("avatars")
        for result in results:
            if "pro_user_id" in result:
                result["therapist_id"] = result.pop("pro_user_id")
        return results

    def update_avatar(self, avatar_id: str, update_data: Dict) -> Dict:
        """Update avatar"""
        avatar = self.get_avatar_by_id(avatar_id)
        if avatar:
            avatar.update(update_data)
            return self.put_item("avatars", avatar)
        return None

    # ========== AI MINDS ==========

    def create_ai_mind(self, mind_data: Dict) -> Dict:
        """Create a new AI Mind"""
        return self.put_item("ai_minds", mind_data)

    def get_ai_mind_by_id(self, mind_id: str) -> Optional[Dict]:
        """Get AI Mind by ID"""
        return self.get_item("ai_minds", {"id": mind_id})

    def get_ai_minds_by_user(self, user_id: str) -> List[Dict]:
        """Get all AI Minds for a user"""
        return self.query_by_index("ai_minds", "user_id-index", "user_id", user_id)

    def get_ai_minds_by_avatar(self, avatar_id: str) -> List[Dict]:
        """Get all AI Minds for an avatar"""
        return self.query_by_index("ai_minds", "avatar_id-index", "avatar_id", avatar_id)

    def get_ai_mind_by_user_avatar(self, user_id: str, avatar_id: str) -> Optional[Dict]:
        """Get AI Mind by user_id and avatar_id pair"""
        minds = self.get_ai_minds_by_user(user_id)
        for mind in minds:
            if mind.get("avatar_id") == avatar_id:
                return mind
        return None

    def get_ai_minds_by_therapist(self, therapist_id: str) -> List[Dict]:
        """Get all AI Minds for a therapist by querying through their avatars"""
        # Get all avatars for this therapist
        avatars = self.get_avatars_by_pro(therapist_id)
        all_minds = []

        # Get AI Minds for each avatar
        for avatar in avatars:
            minds = self.get_ai_minds_by_avatar(avatar["id"])
            all_minds.extend(minds)

        return all_minds

    # ========== PSVS PROFILES ==========

    def create_psvs_profile(self, profile_data: Dict) -> Dict:
        """Create a new PSVS profile"""
        return self.put_item("psvs_profiles", profile_data)

    def get_psvs_profile(self, mind_id: str) -> Optional[Dict]:
        """Get PSVS profile by mind_id"""
        return self.get_item("psvs_profiles", {"mind_id": mind_id})

    def update_psvs_profile(self, mind_id: str, profile_data: Dict) -> Dict:
        """Update PSVS profile"""
        return self.put_item("psvs_profiles", profile_data)

    # ========== CONVERSATION SESSIONS ==========

    def create_session(self, session_data: Dict) -> Dict:
        """Create a new conversation session"""
        return self.put_item("sessions", session_data)

    def get_session_by_id(self, session_id: str) -> Optional[Dict]:
        """Get session by ID"""
        return self.get_item("sessions", {"id": session_id})

    def get_sessions_by_user(self, user_id: str) -> List[Dict]:
        """Get all sessions for a user"""
        return self.query_by_index("sessions", "user_id-index", "user_id", user_id)

    def get_sessions_by_mind(self, mind_id: str) -> List[Dict]:
        """Get all sessions for an AI Mind"""
        return self.query_by_index("sessions", "mind_id-index", "mind_id", mind_id)

    def update_session(self, session_id: str, update_data: Dict) -> Dict:
        """Update session"""
        session = self.get_session_by_id(session_id)
        if session:
            session.update(update_data)
            return self.put_item("sessions", session)
        return None

    # ========== CONVERSATION MESSAGES ==========

    def create_message(self, message_data: Dict) -> Dict:
        """Create a new message"""
        return self.put_item("messages", message_data)

    def get_message_by_id(self, message_id: str) -> Optional[Dict]:
        """Get message by ID"""
        return self.get_item("messages", {"id": message_id})

    def get_messages_by_session(self, session_id: str) -> List[Dict]:
        """Get all messages for a session"""
        messages = self.query_by_index("messages", "session_id-index", "session_id", session_id)
        # Sort by timestamp
        return sorted(messages, key=lambda x: x.get("timestamp", ""))

    # ========== CLIENT-AVATAR CONNECTIONS ==========

    def create_connection(self, connection_data: Dict) -> Dict:
        """Create a new client-avatar connection
        Note: Expects 'client_user_id' field (database field name)
        """
        return self.put_item("connections", connection_data)

    def get_connection_by_id(self, connection_id: str) -> Optional[Dict]:
        """Get connection by ID"""
        return self.get_item("connections", {"id": connection_id})

    def get_connections_by_client(self, client_user_id: str) -> List[Dict]:
        """Get all connections for a client
        Returns connections with 'client_user_id' field (database field name)
        """
        return self.query_by_index("connections", "client_user_id-index", "client_user_id", client_user_id)

    def get_connections_by_avatar(self, avatar_id: str) -> List[Dict]:
        """Get all connections for an avatar"""
        return self.query_by_index("connections", "avatar_id-index", "avatar_id", avatar_id)

    # ========== INVITATIONS ==========

    def create_invitation(self, invitation_data: Dict) -> Dict:
        """Create a new invitation
        Maps therapist_id → pro_user_id for database storage
        """
        data = invitation_data.copy()
        if "therapist_id" in data:
            data["pro_user_id"] = data.pop("therapist_id")
        return self.put_item("invitations", data)

    def get_invitation_by_code(self, code: str) -> Optional[Dict]:
        """Get invitation by code
        Maps pro_user_id → therapist_id for application use
        """
        result = self.get_item("invitations", {"code": code})
        if result and "pro_user_id" in result:
            result["therapist_id"] = result.pop("pro_user_id")
        return result

    def get_invitations_by_pro(self, pro_user_id: str) -> List[Dict]:
        """Get all invitations for a therapist
        Maps pro_user_id → therapist_id for application use
        """
        results = self.query_by_index("invitations", "pro_user_id-index", "pro_user_id", pro_user_id)
        for result in results:
            if "pro_user_id" in result:
                result["therapist_id"] = result.pop("pro_user_id")
        return results

    def get_all_invitations(self) -> List[Dict]:
        """Get all invitations (for portal/stats)
        Maps pro_user_id → therapist_id for application use
        """
        results = self.scan_table("invitations")
        for result in results:
            if "pro_user_id" in result:
                result["therapist_id"] = result.pop("pro_user_id")
        return results

    # ========== REFRESH TOKENS ==========

    def create_refresh_token(self, token: str, user_id: str, role: str):
        """Store a refresh token"""
        return self.put_item("refresh_tokens", {
            "token": token,
            "user_id": user_id,
            "role": role,
            "created_at": datetime.now().isoformat()
        })

    def get_refresh_token(self, token: str) -> Optional[Dict]:
        """Get refresh token data"""
        return self.get_item("refresh_tokens", {"token": token})

    def delete_refresh_token(self, token: str):
        """Delete a refresh token"""
        self.delete_item("refresh_tokens", {"token": token})

# Create a global instance
db = DynamoDBManager()
