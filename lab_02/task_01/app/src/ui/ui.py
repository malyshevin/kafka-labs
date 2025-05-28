import eventlet
eventlet.monkey_patch()
from flask import Flask, render_template, request, session, redirect, url_for
from flask_socketio import SocketIO, emit, join_room
from services.external_msg_handler import (
    create_producer,
    create_consumer,
    send_block_user_message,
    send_chat_message,
    send_ban_word_message,
    receive_chat_message,
)
from services.utils import logger, get_new_user_id


app = Flask(__name__)
app.config["SECRET_KEY"] = "some_secret"
socketio = SocketIO(app)
producer = create_producer()


def receive_messages(socketio):
    try:
        consumer = create_consumer("filtered_messages", default_group_id="chat")
    except Exception as e:
        logger.error(f"Kafka consumer creation failed: {e}")
        return
    for key, msg in receive_chat_message(consumer):
        if not msg or not isinstance(msg, dict):
            logger.warning(f"Skipping empty or incorrect message: {msg}")
            continue
        user_room = msg.get("to_id")
        if not user_room:
            logger.warning(f"No target room ID in message: {msg}")
            continue
        socketio.emit("new_message", msg, room=user_room)


@app.route("/", methods=["GET", "POST"])
def index():
    if request.method == "POST":
        user_id = request.form.get("user_id")
        if user_id:
            session["user_id"] = user_id
            return redirect(url_for("chat"))
        return render_template("index.html", error="Нужно ввести ID (целое число)")
    return render_template("index.html")


@app.route("/register")
def register():
    session["user_id"] = get_new_user_id("last_user_id.txt")
    return redirect(url_for("chat"))


@app.route("/chat")
def chat():
    if "user_id" not in session:
        return redirect(url_for("index"))
    return render_template("chat.html", user_id=session["user_id"])


@app.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("index"))


@socketio.on("join")
def handle_join(data):
    user_id = data["user_id"]
    join_room(str(user_id))


@socketio.on("send_message")
def handle_send_message(data):
    from_id = data.get("from_id")
    to_id = data.get("to_id")
    text = data.get("text")
    try:
        send_chat_message(producer, str(from_id), str(to_id), str(text))
        emit("message_sent", {"ok": True}, to=request.sid)
    except Exception as e:
        emit("message_sent", {"ok": False, "error": str(e)}, to=request.sid)


@socketio.on("block_user")
def handle_block_user(data):
    user_id = data.get("user_id")
    block_id = data.get("block_id")
    try:
        send_block_user_message(producer, str(user_id), str(block_id), action="add")
        emit("block_user_result", {"ok": True, "block_id": block_id}, to=request.sid)
    except Exception as e:
        emit("block_user_result", {"ok": False, "error": str(e)}, to=request.sid)


@socketio.on("unblock_user")
def handle_unblock_user(data):
    user_id = data.get("user_id")
    block_id = data.get("block_id")
    try:
        send_block_user_message(producer, str(user_id), str(block_id), action="remove")
        emit("unblock_user_result", {"ok": True, "block_id": block_id}, to=request.sid)
    except Exception as e:
        emit("unblock_user_result", {"ok": False, "error": str(e)}, to=request.sid)


@socketio.on("ban_word")
def handle_ban_word(data):
    word = data.get("word")
    try:
        send_ban_word_message(producer, str(word), action="add")
        emit("ban_word_result", {"ok": True, "word": word}, to=request.sid)
    except Exception as e:
        emit("ban_word_result", {"ok": False, "error": str(e)}, to=request.sid)


@socketio.on("unban_word")
def handle_unban_word(data):
    word = data.get("word")
    try:
        send_ban_word_message(producer, str(word), action="remove")
        emit("unban_word_result", {"ok": True, "word": word}, to=request.sid)
    except Exception as e:
        emit("unban_word_result", {"ok": False, "error": str(e)}, to=request.sid)


if __name__ == "__main__":
    socketio.start_background_task(receive_messages, socketio)
    socketio.run(app, host='0.0.0.0', port=5000)
