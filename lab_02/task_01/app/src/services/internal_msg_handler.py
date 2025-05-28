"""
    Внутренний обработчик сообщений. Занимается фильтрацией, блокировкой, а также цензурированием.
"""
import re
import faust
from services.utils import (
    logger,
    get_env,
)

app = faust.App(
    "external_message_handler",
    broker=get_env("KAFKA_BOOTSTRAP_SERVERS", "kafka://localhost:9092"),
    store=get_env("KAFKA_MEMORY_TYPE", "memory://")
)


class Message(faust.Record, serializer="json"):
    from_id: str
    to_id: str
    text: str


class BlockCommand(faust.Record, serializer="json"):
    user_id: str
    blocked_user_id: str
    action: str  # add или remove


class WordCommand(faust.Record, serializer="json"):
    word: str
    action: str  # add или remove


### Таблицы состояния (Stateful Tables)

blocked_list_table = app.Table("blocked_list", default=lambda: set(), partitions=3)    # пользователь -> set заблокированных
banned_words_table = app.Table("banned_words", default=lambda: list(), partitions=3)   # список запрещённых слов


### Агент для обновления списка заблокированных пользователей
@app.agent(app.topic("blocked_users", value_type=BlockCommand))
async def update_blocked_list(commands):
    async for cmd in commands:
        user_id_block_set = set(blocked_list_table[cmd.user_id])
    
        if cmd.action == "add":
            user_id_block_set.add(cmd.blocked_user_id)

        if cmd.action == "remove":
            user_id_block_set.discard(cmd.blocked_user_id)

        blocked_list_table[cmd.user_id] = user_id_block_set
        logger.info(f'🟩 [Blocked user] {cmd.user_id} -> {blocked_list_table[cmd.user_id]}')
        yield


### Агент для обновления списка запрещенных слов
@app.agent(app.topic("banned_words", value_type=WordCommand))
async def update_banned_words(commands):
    async for cmd in commands:
        words = set(banned_words_table["words"])

        if cmd.action == "add":
            words.add(cmd.word.lower())

        if cmd.action == "remove":
            words.discard(cmd.word.lower())

        banned_words_table["words"] = list(words)
        logger.info(f"🟩 [Banned words] {banned_words_table['words']}")


### Цензурирующая функция
def censor(text, banned):
    for w in banned:
        text = re.sub(r'(?i)'+re.escape(w), '*'*len(w), text)
    return text


### Главный поток обработки сообщений
@app.agent(app.topic("messages", value_type=Message))
async def process_messages(messages):
    async for msg in messages:
        recipient_blocked = blocked_list_table.get(msg.to_id, set())

        if msg.from_id in recipient_blocked:
            logger.info(f"⛔️ [Blocked users] {msg.from_id} заблокирован у {msg.to_id}. Сообщение удалено.")
            continue

        banned = set(banned_words_table["words"])
        censored = censor(msg.text, banned)

        filtered_message = Message(from_id=msg.from_id, to_id=msg.to_id, text=censored)
        await app.send("filtered_messages", value=filtered_message)

        logger.info(f"🟩 [Filtered messages] {filtered_message}")


if __name__ == "__main__":
    app.main()
