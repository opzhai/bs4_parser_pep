# Проект parser_yap

## Режим работы whats-new поможет быть в курсе важных изменений между основными версиями Python:
соберет ссылки на статьи о нововведениях;
достанет из них справочную информацию (имя автора или редактора статьи) 

## Режим работы latest-versions - парсер, который будет собирать информацию о версиях Python:
собирает номера, статусы (in development, pre-release, stable и так далее)
собирает ссылки на документацию.

## Режим работы pep:
спарсит данные обо всех документах PEP;
сравнит статус на странице PEP со статусом в общем списке;
осчитает количество PEP в каждом статусе и общее количество PEP; данные о статусе документа нужно брать со страницы каждого PEP, а не из общей таблицы;
сохранит результат в табличном виде в csv-файл.
