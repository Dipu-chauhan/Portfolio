from datetime import datetime, timezone
import os

from flask import Flask, jsonify, render_template, request
from bson import ObjectId
from bson.errors import InvalidId
from pymongo import MongoClient
from pymongo.errors import PyMongoError

app = Flask(__name__)


MONGO_URI = os.getenv("MONGO_URI", "mongodb://localhost:27017/")
mongo_client = MongoClient(MONGO_URI)
contact_collection = mongo_client["portfolio"]["messages"]


@app.route('/')
def index():
    return render_template('index.html')


@app.post("/api/contact")
def save_contact_message():
    payload = request.get_json(silent=True) or {}

    name = str(payload.get("name", "")).strip()
    email = str(payload.get("email", "")).strip()
    message = str(payload.get("message", "")).strip()

    if not name or not email or not message:
        return jsonify({"ok": False, "message": "Name, email, and message are required."}), 400

    doc = {
        "name": name,
        "email": email,
        "message": message,
        "created_at": datetime.now(timezone.utc).isoformat(),
    }

    try:
        result = contact_collection.insert_one(doc)
    except PyMongoError:
        return jsonify({"ok": False, "message": "Could not save message to database."}), 500

    return jsonify(
        {
            "ok": True,
            "message": "Message saved successfully.",
            "id": str(result.inserted_id),
        }
    ), 201


@app.get("/messages")
def admin_messages_page():
    return render_template("admin.html")


@app.get("/api/admin/messages")
def get_admin_messages():
    try:
        docs = contact_collection.find().sort("created_at", -1)
        messages = [
            {
                "id": str(doc.get("_id")),
                "name": doc.get("name", ""),
                "email": doc.get("email", ""),
                "message": doc.get("message", ""),
                "created_at": doc.get("created_at", ""),
            }
            for doc in docs
        ]
    except PyMongoError:
        return jsonify({"ok": False, "message": "Could not fetch messages."}), 500

    return jsonify({"ok": True, "messages": messages}), 200


@app.delete("/api/admin/messages/<message_id>")
def delete_admin_message(message_id):
    try:
        object_id = ObjectId(message_id)
    except InvalidId:
        return jsonify({"ok": False, "message": "Invalid message id."}), 400

    try:
        result = contact_collection.delete_one({"_id": object_id})
    except PyMongoError:
        return jsonify({"ok": False, "message": "Could not delete message."}), 500

    if result.deleted_count == 0:
        return jsonify({"ok": False, "message": "Message not found."}), 404

    return jsonify({"ok": True, "message": "Message deleted successfully."}), 200


if __name__ == '__main__':
    app.run(debug=True)

