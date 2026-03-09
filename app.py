from flask import Flask, request, jsonify , render_template
import boto3
import os
from dotenv import load_dotenv
from botocore.config import Config

load_dotenv()

app = Flask(__name__)

TABLE_NAME = "Notes"


def get_table():
    config = Config(
        retries={
            "max_attempts": 2,
            "mode": "standard"
        },
        connect_timeout=5,
        read_timeout=5
    )

    dynamodb = boto3.resource(
        "dynamodb",
        aws_access_key_id=os.environ.get("AWS_ACCESS_KEY_ID"),
        aws_secret_access_key=os.environ.get("AWS_SECRET_ACCESS_KEY"),
        region_name=os.environ.get("AWS_DEFAULT_REGION"),
        endpoint_url=os.environ.get("DYNAMODB_ENDPOINT"),  # optional
        config=config
    )

    return dynamodb.Table(TABLE_NAME)


@app.route("/notes", methods=["GET"])
def get_notes():
    try:
        table = get_table()
        response = table.scan(Limit=20)
        return jsonify(response.get("Items", []))
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route("/notes", methods=["POST"])
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

        return jsonify({"id": note_id, "content": data["content"]}), 201

    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route("/notes/<note_id>", methods=["DELETE"])
def delete_note(note_id):
    try:
        table = get_table()
        table.delete_item(Key={"id": note_id})
        return jsonify({"deleted": note_id})
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route("/")
def home():
    return render_template("index.html")


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
