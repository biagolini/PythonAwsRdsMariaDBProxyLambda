import os
import json
import pymysql
import boto3
import logging
from datetime import datetime
from botocore.exceptions import ClientError

logger = logging.getLogger()
logger.setLevel(logging.INFO)

# Environment variables (configure in Lambda console or via IaC)
DB_SECRET_NAME = os.environ.get("DB_SECRET_NAME")            # e.g. "lambda_user-mariadb-secret"
DB_PROXY_ENDPOINT = os.environ.get("DB_PROXY_ENDPOINT")      # e.g. "mariadb-proxy.proxy-xxxxxx.rds.amazonaws.com"
DB_NAME = os.environ.get("DB_NAME", "customerdb")
DB_TABLE = os.environ.get("DB_TABLE", "users")
DB_PORT = int(os.environ.get("DB_PORT", "3306"))

# Load credentials from Secrets Manager
def get_db_credentials(secret_name):
    client = boto3.client("secretsmanager")
    try:
        response = client.get_secret_value(SecretId=secret_name)
        secret = json.loads(response["SecretString"])
        return secret["username"], secret["password"]
    except ClientError as e:
        logger.error(f"Unable to retrieve secret: {e}")
        raise e

# Create reusable DB connection (connection pooling is not native in Lambda)
def get_db_connection():
    username, password = get_db_credentials(DB_SECRET_NAME)
    return pymysql.connect(
        host=DB_PROXY_ENDPOINT,
        user=username,
        password=password,
        db=DB_NAME,
        port=DB_PORT,
        connect_timeout=5,
        cursorclass=pymysql.cursors.DictCursor,
    )

# JSON serializer for datetime
def default_serializer(obj):
    if isinstance(obj, datetime):
        return obj.isoformat()
    raise TypeError(f"Type {type(obj)} not serializable")

# Standard API response
def response(status_code, body):
    return {
        "statusCode": status_code,
        "headers": {
            "Content-Type": "application/json",
            "Access-Control-Allow-Origin": "*",
            "Access-Control-Allow-Methods": "OPTIONS,GET,POST,PUT,DELETE",
            "Access-Control-Allow-Headers": "Content-Type",
        },
        "body": json.dumps(body, default=default_serializer)
    }

# Lambda handler
def lambda_handler(event, context):
    http_method = event.get("httpMethod", "")
    query = event.get("queryStringParameters") or {}
    try:
        body = json.loads(event.get("body") or "{}")
    except json.JSONDecodeError:
        return response(400, {"error": "Invalid JSON payload"})

    user_id = query.get("id")

    try:
        conn = get_db_connection()
        with conn.cursor() as cursor:

            match http_method:
                case "GET":
                    if not user_id:
                        return response(400, {"error": "Missing 'id' parameter"})
                    cursor.execute(f"SELECT * FROM {DB_TABLE} WHERE id = %s", (user_id,))
                    user = cursor.fetchone()
                    return response(200, user) if user else response(404, {"error": "User not found"})

                case "POST":
                    name = body.get("name")
                    email = body.get("email")
                    if not name or not email:
                        return response(400, {"error": "Missing 'name' or 'email'"})
                    cursor.execute(f"INSERT INTO {DB_TABLE} (name, email) VALUES (%s, %s)", (name, email))
                    conn.commit()
                    return response(201, {"message": "User created"})

                case "PUT":
                    if not user_id:
                        return response(400, {"error": "Missing 'id' parameter"})
                    name = body.get("name")
                    email = body.get("email")
                    if not name or not email:
                        return response(400, {"error": "Missing 'name' or 'email'"})
                    cursor.execute(f"UPDATE {DB_TABLE} SET name = %s, email = %s WHERE id = %s", (name, email, user_id))
                    conn.commit()
                    return response(200, {"message": f"User {user_id} updated"})

                case "DELETE":
                    if not user_id:
                        return response(400, {"error": "Missing 'id' parameter"})
                    cursor.execute(f"DELETE FROM {DB_TABLE} WHERE id = %s", (user_id,))
                    conn.commit()
                    return response(200, {"message": f"User {user_id} deleted"})

                case _:
                    return response(405, {"error": f"Method {http_method} not allowed"})

    except Exception as e:
        logger.exception("Database operation failed")
        return response(500, {"error": str(e)})

    finally:
        if 'conn' in locals():
            conn.close()
