## Задание 1

**Цель**: создать систему обработки потоков сообщений с функциональностью блокировки пользователей и цензуры сообщений.

**Задачи**:

1. Реализовать систему потоковой передачи сообщений с возможностью:

    - Блокировки пользователей друг другом (фильтрация сообщений от нежелательных отправителей).
    - Автоматической цензуры сообщений по обновляемому списку запрещённых слов.

2. Организовать хранение списков заблокированных пользователей и запрещённых слов.
3. Настроить инфраструктуру c использованием Docker-compose и Kafka с нужными топиками.
4. Провести тестирование работы системы с помощью подготовленных тестовых данных.

### Быстрый старт

Структура проекта

![img](docs/kafka_lab_02.svg)

Структура директорий

```
|_ task_01
  |_ app
    |_ src
      |_ services
        |_ external_msg_handler.py      # отправка / чтение сообщений кафка <--> UI-я 
        |_ internal_msg_handler.py      # обработка сообщений внутри кафки (цензура, блокировка)
      |_ ui                             # web морда удобства тестирования
    |_ Dockerfile
    |_ pyproject.toml
  |_ docker-compose-app.yml             # запуск приложения
  |_ docker-compose-cluster.yml         # запуск кластера
```

Команды запуска

```bash
# запустить кластер
docker-compose -f docker-compose-cluster.yml up -d

# создаем топики
docker ps
docker exec -it <container_id_kafka> /bin/sh
cd /opt/bitnami/kafka/bin

kafka-topics.sh --create --topic messages --bootstrap-server localhost:9092 --partitions 3 --replication-factor 2 
kafka-topics.sh --create --topic blocked_users --bootstrap-server localhost:9092 --partitions 3 --replication-factor 2
kafka-topics.sh --create --topic filtered_messages --bootstrap-server localhost:9092 --partitions 3 --replication-factor 2
kafka-topics.sh --create --topic banned_words --bootstrap-server localhost:9092 --partitions 3 --replication-factor 2

# запустить приложение
docker-compose -f docker-compose-app.yml up
```

В результате в [UI](http://localhost:8080) можно будет увидеть следующие топики и таблицы

![img](docs/ui.png)

По адресу http://localhost:5000 будет доступен UI чата.

![img](docs/chat.png)

### Тестирование

Зайдем в приложение (один "пользователь" через обычный браузер, другой в режиме инкогнито).

![img](docs/register_2_users.png)

#### Обычная отправка сообщения

Попробуем отправить сообщение от пользователя 1 к пользователю 2.

![img](docs/simple_message.png)

В обратную сторону

![img](docs/simple_message2.png)

#### Блокировка и разблокировка пользователя

Пользователь 1 блокирует пользователя 2.

![img](docs/block_user2.png)

Пользователь 2 пытается отправить сообщение пользователю 1. У него не получается.

![img](docs/check_block_user.png)

Сообщение в логах, о том, что сообщение было удалено.

![img](docs/log_block_user.png)

Пользователь 1 разблокировал пользователя 2.

![img](docs/unblock_user2.png)

Пользователь 2 пытается отправить сообщение пользователю 1. У него получается.

![img](docs/check_unblock_user.png)

### Список цензурированных слов

Блокируем слово 'bad word'.

![img](docs/block_word.png)

Пользователь 1 отправляет сообщение пользователю 2 с плохим словом. Слово заменяется на ***.

![img](docs/check_block_word.png)

Разблокируем слово 'bad word'

![img](docs/unblock_word.png)

Пользователь 1 отправляет сообщение пользователю 2 с плохим словом. Слово остается как есть.

![img](docs/check_unblock_word.png)
