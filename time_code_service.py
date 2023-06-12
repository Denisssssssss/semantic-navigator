from youtube_transcript_api import YouTubeTranscriptApi
from lemmagen3 import Lemmatizer
from natasha import NamesExtractor, MorphVocab, Segmenter, Doc, NewsEmbedding, NewsNERTagger, PER
from SPARQLWrapper import SPARQLWrapper, JSON
import spacy

import TimeCodedWord
import time
import re
import collections

lemmatizer = Lemmatizer('ru')

vocab = MorphVocab()
ext = NamesExtractor(vocab)
emb = NewsEmbedding()
tagger = NewsNERTagger(emb)
segm = Segmenter()

nlp = spacy.load('ru_core_news_lg')


def get_time_codes(video_id: str, key_words: list):
    st = time.time()
    transcription = get_transcription(video_id)
    lemmas = lemmatize(transcription)
    names = extract_names(transcription)
    terms = onto_math_pro()
    # total = merge_words(names, key_words, terms)
    response = align_time_codes(lemmas, key_words, names, terms)
    stats(response.keys(), names, key_words, terms)
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


# def merge_words(names, key_words, terms):
#     words = list()
#     for name in names:
#         if len(words) == 0:
#             words.append(name)
#             continue
#         for word in words:
#             if name.lower() != word.lower():
#                 words.append(name)
#     for key_word in key_words:
#         if len(words) == 0:
#             words.append(key_word)
#             continue
#         for word in words:
#             if key_word.lower() != word.lower():
#                 words.append(key_word)
#     for term in terms:
#         if len(words) == 0:
#             words.append(term)
#             continue
#         for word in words:
#             if term.lower() != word.lower():
#                 words.append(term)
#     return words


def extract_names(transcription_entries):
    names = list()
    segments = ' '.join(entry['text'] for entry in transcription_entries)
    doc = nlp(segments)
    for entity in doc.ents:
        if entity.label_ == 'PER' and lemmatizer.lemmatize(entity.text) not in names:
            name = capitalize(entity.lemma_)
            max = 0
            for valid_name in valid_names():
                k = string_jaccard(valid_name, name)
                if k > 0.5 and k > max and valid_name not in names:
                    names.append(valid_name)

    print(f'NER total: {len(names)}')
    return names


def valid_names():
    return ['Коши', 'Эйлер', 'Галилей', 'Кострикин', 'Гаусс', 'Лагранж', 'Риман',
            'Гилберт', 'Абель', 'Лобачевский', 'Чебышев', 'Декарт', 'Ньютон', 'Диофант', 'Кеплер', 'Птолемей',
            'Тарталья', 'Галуа', 'Бомбелли', 'Руффини', 'Кардан', 'Феррари']

# def fix_ner(time_codes, names, lemmas):
#     result = collections.defaultdict(list)
#     for name in names:
#         if len(time_codes[name]) > 1:
#             for x in time_codes[name]:
#                 result[name].append(x)
#     for lemma in lemmas:
#         for x in time_codes[lemma]:
#             result[lemma].append(x)
#     return result


def capitalize(words):
    return ' '.join(word.capitalize() for word in words.split(" "))


def onto_math_pro():
    terms = list()
    with open('terms.txt') as file:
        for line in file:
            if len(line.rstrip().split()) < 3:
                terms.append(line.rstrip().replace('\"', ''))
    print(f'available terms: {len(terms)}')
    return terms


terms = onto_math_pro()

def get_transcription(video_id):
    if timecodes_exists(video_id):
        return find_processed_time_codes(video_id)
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


def timecodes_exists(video_id):
    return False


def find_processed_time_codes(video_id):
    return list()


def save_time_codes(video_id, time_codes):
    print(f'saved for {video_id}')


def align_time_codes(time_codes: list, key_words: list, names: list, terms: list):
    st = time.time()
    result = collections.defaultdict(set)

    for word in terms:
        lemma = ' '.join([lemmatizer.lemmatize(token) for token in word.split()])
        ans = list()
        tc = list()
        count = 0
        for x in time_codes:
            if hash(x.word.lower()) == hash(lemma.split(' ')[count].lower()) and string_jaccard(x.word.lower(), lemma.split(' ')[count].lower()) > .75:
                count += 1
                ans.append(word)
                tc.append(x)
                if len(ans) == len(lemma.split(' ')):
                    result[word].add(tc[0].time)
                    ans = list()
                    count = 0
            else:
                ans = list()
                count = 0
    for word in names:
        lemma = ' '.join([lemmatizer.lemmatize(token) for token in word.split()])
        ans = list()
        count = 0
        for x in time_codes:
            if hash(x.word.lower()) == hash(lemma.split(' ')[count].lower()) and x.word.lower() == lemma.split(' ')[count].lower():
                count += 1
                ans.append(x)
                if len(ans) == len(lemma.split(' ')):
                    result[word].add(ans[0].time)
                    ans = list()
                    count = 0
            else:
                ans = list()
                count = 0
    for word in key_words:
        lemma = ' '.join([lemmatizer.lemmatize(token) for token in word.split()])
        ans = list()
        count = 0
        for x in time_codes:
            if hash(x.word.lower()) == hash(lemma.split(' ')[count].lower()) and x.word.lower() == lemma.split(' ')[count].lower():
                count += 1
                ans.append(x)
                if len(ans) == len(lemma.split(' ')):
                    result[word].add(ans[0].time)
                    ans = list()
                    count = 0
            else:
                ans = list()
                count = 0
    end = time.time()
    print('total time for align:', end - st)

    return sort_dict(result)


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
    union = (len(list1) + len(list2)) - intersection
    return float(intersection) / union


def string_jaccard(str1, str2):
    return jaccard(list(str1), list(str2))