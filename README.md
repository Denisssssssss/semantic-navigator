В терминале:

!pip3 install spacy
!pip3 install mysql
!pip3 install lemmagen3
!pip3 install youtube_transcript_api
!pip3 install spacy
python3 -m spacy download ru_core_news_lg

База данных:
MySQL, user=root, database=sem_nav_db

надо запустить в бд 3 sql файла: names.sql, terms.sql, responses.sql

Запросы:
GET localhost:8000/api/v1/timecode/{идентификатор_видео_на_youtube}?key_words=[список ключевых слов разделенных запятой с пробелом]

Для страниц:
добавить блок со скриптами из файла scripts.html
тег iframe, содержащий плеер youtube обернуть в еще один тег div по образцу из файла responsive_container.html

После доработки страниц при открытии страницы будет отправляться запрос в приложение и под видео отобразятся тайм-коды