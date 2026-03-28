from flask import Flask, request, jsonify, render_template
import boto3
import os
from dotenv import load_dotenv
from botocore.config import Config
import redis
import logging
import json
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address

load_dotenv()

app = Flask(__name__)

# -------------------------
# 🔴 REDIS (Caching)
# -------------------------
redis_client = redis.Redis(
    host='localhost',
    port=6379,
    db=0,
    decode_responses=True
)

# -------------------------
# 🚦 RATE LIMITING
# -------------------------
limiter = Limiter(
    get_remote_address,
    app=app,
    default_limits=["100 per 15 minutes"]
)

# -------------------------
# 📊 LOGGING
# -------------------------
logging.basicConfig(
    filename='app.log',
    level=logging.INFO,
    format='%(asctime)s %(levelname)s %(message)s'
)

TABLE_NAME = "Notes"


def get_table():
    config = Config(
        retries={"max_attempts": 2, "mode": "standard"},
        connect_timeout=5,
        read_timeout=5
    )

    dynamodb = boto3.resource(
        "dynamodb",
        aws_access_key_id=os.environ.get("AWS_ACCESS_KEY_ID"),
        aws_secret_access_key=os.environ.get("AWS_SECRET_ACCESS_KEY"),
        region_name=os.environ.get("AWS_DEFAULT_REGION"),
        endpoint_url=os.environ.get("DYNAMODB_ENDPOINT"),
        config=config
    )

    return dynamodb.Table(TABLE_NAME)


# -------------------------
# 📥 GET NOTES (WITH CACHE)
# -------------------------
@app.route("/notes", methods=["GET"])
@limiter.limit("50 per minute")
def get_notes():
    try:
        cache_key = "notes"

        # ✅ Check cache first
        cached = redis_client.get(cache_key)
        if cached:
            logging.info("Cache hit for /notes")
            return jsonify(json.loads(cached))  # simple parse

        # ❌ Cache miss → fetch DB
        logging.info("Cache miss for /notes")

        table = get_table()
        response = table.scan(Limit=20)
        items = response.get("Items", [])

        # ✅ Store in cache (60 sec)
        redis_client.setex(cache_key, 60, json.dumps(items))

        return jsonify(items)

    except Exception as e:
        logging.error(f"Error in GET /notes: {str(e)}")
        return jsonify({"error": str(e)}), 500


# -------------------------
# ✍️ CREATE NOTE
# -------------------------
@app.route("/notes", methods=["POST"])
@limiter.limit("20 per minute")
def create_note():
    try:
        data = request.get_json()

        if not data or "content" not in data:
            return jsonify({"error": "Missing content"}), 400

        table = get_table()
        note_id = os.urandom(8).hex()

        table.put_item(Item={
            "id": note_id,
            "content": data["content"]
        })

        # ❗ Invalidate cache after write
        redis_client.delete("notes")

        logging.info(f"Created note {note_id}")

        return jsonify({"id": note_id, "content": data["content"]}), 201

    except Exception as e:
        logging.error(f"Error in POST /notes: {str(e)}")
        return jsonify({"error": str(e)}), 500
