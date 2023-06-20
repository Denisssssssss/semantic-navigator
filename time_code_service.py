import collections
import re
import time

import json
import spacy
from mysql.connector import connect
from lemmagen3 import Lemmatizer
from youtube_transcript_api import YouTubeTranscriptApi
import TimeCodedWord
import json


lemmatizer = Lemmatizer('ru')
nlp = spacy.load('ru_core_news_lg')
# conn = psycopg2.connect(dbname='sem_nav_db', user='root', host='localhost')
# cursor = conn.cursor()
connection = connect(host='localhost', user='root', database='sem_nav_db')
cursor = connection.cursor()


def get_time_codes(video_id: str, key_words: list):
    st = time.time()
    if timecodes_exists(video_id):
        return find_processed_time_codes(video_id)
    transcription = get_transcription(video_id)
    lemmas = lemmatize(transcription)
    names = extract_names(transcription)
    terms = onto_math_pro()
    response = align_time_codes(lemmas, key_words, names, terms)
    # stats(response.keys(), names, key_words, terms)
    save_time_codes(video_id, response)
    end = time.time()
    print('finished in', end - st)
    print('\n')

    return response


def merge_words(names, key_words, terms):
    words = list()
    for name in names:
        words.append(name)
    for key_word in key_words:
        words.append(key_word)
    for term in terms:
        words.append(term)
    return words


def extract_names(transcription_entries):
    names = list()
    segments = ' '.join(entry['text'] for entry in transcription_entries)
    doc = nlp(segments)
    ners = valid_names()
    for entity in doc.ents:
        if entity.label_ == 'PER' and lemmatizer.lemmatize(entity.text) not in names:
            name = capitalize(entity.lemma_)
            max = 0
            for valid_name in ners:
                k = string_jaccard(valid_name, name)
                if k > 0.75 and k > max and valid_name not in names:
                    names.append(valid_name)

    print(f'NER total: {len(names)}')
    return names


def valid_names():
    cursor.execute('select value from r_names;')
    names = list()
    for row in cursor:
        names.append(row[0])
    return names


def capitalize(words):
    return ' '.join(word.capitalize() for word in words.split(" "))


def onto_math_pro():
    start = time.time()
    terms = list()
    cursor.execute('select value from terms;')
    for row in cursor:
        terms.append(row[0])
    print(f'available terms: {len(terms)}')
    print(f'Terms got in {time.time() - start}')
    return terms


def get_transcription(video_id):
    transcript_list = YouTubeTranscriptApi.list_transcripts(video_id)
    gen_transcript = transcript_list.find_generated_transcript(['ru', 'ru'])
    return gen_transcript.fetch()


def lemmatize(text_segments):
    time_coded_words = list()
    total = 0
    elapsed = 0
    regex = re.compile('[а-яА-Я]')

    for entry in text_segments:
        text = entry['text']
        words = text.split(' ')
        start = entry['start']
        for word in words:
            if not regex.match(word):
                continue
            st = time.time()
            time_coded_word = TimeCodedWord.TimeCodedWord(lemmatizer.lemmatize(word), start)
            time_coded_words.append(time_coded_word)
            end = time.time()
            elapsed += end - st
            total += 1

    print('average time for lemmatization:', elapsed / total)
    print('total words:', total)
    print('total time for lemmatization:', elapsed)
    return time_coded_words


def timecodes_exists(video_id: str):
    cursor.execute('select exists(select * from responses where id = %s)', (video_id,))
    return cursor.fetchone()[0]


def find_processed_time_codes(video_id):
    cursor.execute('select time_codes from responses where id = %s;', (video_id,))
    time_codes = cursor.fetchone()[0]
    return json.loads(time_codes)


def save_time_codes(video_id, time_codes):
    cursor.execute('insert into responses (id, time_codes) values (%(video_id)s, %(time_codes)s)', {'video_id': video_id, 'time_codes': json.dumps(time_codes)})
    connection.commit()
    print(f'saved for {video_id}')


def align_time_codes(time_codes: list, key_words: list, names: list, terms: list):
    st = time.time()
    result = collections.defaultdict(set)
    find(result, key_words, time_codes)
    find(result, terms, time_codes)
    find(result, names, time_codes)
    end = time.time()
    print('total time for align:', end - st)

    return sort_dict(result)


def find(result, words, time_codes):
    for word in words:
        lemma = ' '.join([lemmatizer.lemmatize(token) for token in word.split()])
        ans = list()
        tc = list()
        count = 0
        for x in time_codes:
            curr_lemma = lemma.split(' ')[count]
            if rabin_carp_equals(x.word, curr_lemma) and string_jaccard(x.word.lower(), curr_lemma.lower()) > .75:
                count += 1
                ans.append(word)
                tc.append(x)
                if len(ans) == len(lemma.split(' ')):
                    result[word].add(tc[0].time)
                    ans = list()
                    count = 0
                    tc = list()
            else:
                ans = list()
                tc = list()
                count = 0
    return result


def sort_dict(result):
    ans = collections.defaultdict(list)
    for word in result.keys():
        ans[word] = sorted(result[word])
    return ans


def stats(keys, names, key_words, terms):
    tnames = 0
    tkwords = 0
    tterms = 0
    for key in keys:
        if key in names:
            tnames += 1
        if key in key_words:
            tkwords += 1
        if key in terms:
            tterms += 1
    print(f'key words: {tkwords}')
    print(f'names: {tnames}')
    print(f'terms: {tterms}')


def jaccard(list1, list2):
    intersection = len(list(set(list1).intersection(list2)))
    union = (len(set(list1)) + len(set(list2))) - intersection
    return float(intersection) / union


def string_jaccard(str1, str2):
    return jaccard(list(str1), list(str2))


def rabin_carp_equals(str1, str2):
    return hash(str1.lower()) == hash(str2.lower())
