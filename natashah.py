from natasha import NamesExtractor, MorphVocab, Doc, NewsEmbedding, NewsNERTagger, Segmenter


text = 'россия'
vocab = MorphVocab()
ext = NamesExtractor(vocab)
doc = Doc(text)
emb = NewsEmbedding()
tagger = NewsNERTagger(emb)
segm = Segmenter()


doc.segment(segm)
doc.tag_ner(tagger)

for name in doc.spans:
    print(name.text)






