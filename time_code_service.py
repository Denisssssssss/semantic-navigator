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
    total = merge_words(names, key_words, terms)
    response = align_time_codes(lemmas, total)
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


# def extract_names(transcription_entries):
#     names = list()
#     segments = ' '.join(entry['text'] for entry in transcription_entries)
#     doc = Doc(capitalize(segments))
#     doc.segment(segm)
#     doc.tag_ner(tagger)
#     for name in doc.spans:
#         if name.type == PER and len(name.text.split(" ")) == 1 and name.text not in names:
#             names.append(name.text)
#     return names


def extract_names(transcription_entries):
    names = list()
    segments = ' '.join(entry['text'] for entry in transcription_entries)
    doc = nlp(segments)
    for entity in doc.ents:
        if entity.label_ == 'PER' and lemmatizer.lemmatize(entity.text) not in names:
            names.append(capitalize(lemmatizer.lemmatize(entity.text)))
    print(f'NER total: {len(names)}')
    return names


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
    sparql = SPARQLWrapper("http://dbpedia.org/sparql")
    queryString = """
        PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>
        SELECT ?label
        WHERE { <http://dbpedia.org/resource/Asturias> rdfs:label ?label }
    """
    sparql.setQuery(queryString)
    sparql.setReturnFormat(JSON)
    results = sparql.query().convert()

    # print(results, "\n")
    return list()


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


def align_time_codes(time_codes: list, key_words: list):
    st = time.time()
    result = collections.defaultdict(set)

    for word in key_words:
        lemma = ' '.join([lemmatizer.lemmatize(token) for token in word.split()])
        ans = list()
        count = 0
        for x in time_codes:
            if x.word.lower() == lemma.split(' ')[count].lower():
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