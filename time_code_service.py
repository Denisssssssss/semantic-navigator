from youtube_transcript_api import YouTubeTranscriptApi
from lemmagen3 import Lemmatizer
from natasha import NamesExtractor, MorphVocab, Segmenter, Doc, NewsEmbedding, NewsNERTagger, PER

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


def get_semantic_time_codes(video_id: str, key_words: list):
    st = time.time()
    time_codes = get_time_codes(video_id)
    names = extract_names(time_codes)
    for name in names:
        if name not in key_words:
            key_words.append(name)
    for word in onto_math_pro():
        if word not in key_words:
            key_words.append(word)
    response = align_time_codes(time_codes, key_words)
    save_time_codes(video_id, response)
    end = time.time()
    print('finished in', end - st)

    return response


def extract_names(time_coded_words):
    full_text = ""
    for word in time_coded_words:
        full_text = full_text + " " + word.word
    doc = Doc(full_text)
    doc.segment(segm)
    doc.tag_ner(tagger)
    names = list()
    for name in doc.spans:
        names.append(name.text)
    return names



def onto_math_pro():
    return list()


def get_time_codes(video_id):
    if timecodes_exists(video_id):
        return find_processed_time_codes(video_id)
    transcript_list = YouTubeTranscriptApi.list_transcripts(video_id)
    gen_transcript = transcript_list.find_generated_transcript(['ru', 'ru'])
    entries = gen_transcript.fetch()
    time_coded_words = list()
    total = 0
    elapsed = 0
    regex = re.compile('[а-яА-Я]')

    for entry in entries:
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
    result = collections.defaultdict(list)

    for word in key_words:
        lemma = ' '.join([lemmatizer.lemmatize(token) for token in word.split()])
        ans = list()
        count = 0
        for x in time_codes:
            if x.word.lower() == lemma.split(' ')[count].lower():
                count += 1
                ans.append(x)
                if len(ans) == len(lemma.split(' ')):
                    result[word].append(ans[0].time)
                    ans = list()
                    count = 0
            else:
                ans = list()
                count = 0
    end = time.time()
    print('total time for align:', end - st)

    return result
