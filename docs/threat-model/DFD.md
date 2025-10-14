# DFD — Data Flow Diagram

## Диаграмма (Mermaid)

```mermaid
flowchart LR
    User[Team Member] -->|F1: HTTPS API Calls| API[Sprint Retros API]

    subgraph "T B: Application Server"
        API -->|F2: DB Connection| DB[(SQLite/Postgres DB)]
    end

    subgraph "T B: User's Browser"
        User
    end
```

## Список потоков

| ID | Откуда → Куда | Канал/Протокол | Данные | Комментарий |
|----|---------------|----------------|--------|-------------|
| F1 | Пользователь → API | HTTPS | JSON с данными ретро (тексты, даты), JWT токен в заголовке | Основной канал взаимодействия с сервисом. |
| F2 | API → База данных | TCP (SQL-протокол) | SQL-запросы, записи о ретроспективах и пользователях | Внутреннее взаимодействие с хранилищем. |
