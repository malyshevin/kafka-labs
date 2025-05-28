CREATE STREAM messages_stream (
    user_id VARCHAR,
    recipient_id VARCHAR,
    message VARCHAR,
    timestamp BIGINT
) WITH (
    KAFKA_TOPIC='messages',
    VALUE_FORMAT='JSON'
);

-- Таблица с общим количеством сообщений
CREATE TABLE total_messages_count AS
SELECT 
    'all' AS key,
    COUNT(*) AS total_messages
FROM messages_stream
GROUP BY 'all'
EMIT CHANGES;

-- Таблица с количеством уникальных получателей среди всех сообщений
CREATE TABLE unique_recipients_count AS
SELECT
    'all' AS key,
    ARRAY_LENGTH(COLLECT_SET(recipient_id)) AS total_unique_recipients
FROM messages_stream
GROUP BY 'all'
EMIT CHANGES;

-- Таблица с количеством сообщений, отправленных каждым пользователем
CREATE TABLE user_messages_count AS
SELECT 
    user_id, 
    COUNT(*) AS sent_messages
FROM messages_stream
GROUP BY user_id
EMIT CHANGES;

-- Таблица с количеством уникальных получателей для каждого пользователя
CREATE TABLE user_unique_recipients AS
SELECT 
    user_id,
    ARRAY_LENGTH(COLLECT_SET(recipient_id)) AS unique_recipients
FROM messages_stream
GROUP BY user_id
EMIT CHANGES;

-- Итоговая таблица user_statistics (агрегированные по каждому пользователю)
CREATE TABLE user_statistics
WITH (
    KAFKA_TOPIC='user_statistics',
    PARTITIONS=1
) AS
    SELECT 
        user_id,
        COUNT(*) AS sent_messages,
        ARRAY_LENGTH(COLLECT_SET(recipient_id)) AS unique_recipients
    FROM messages_stream
    GROUP BY user_id
EMIT CHANGES;
