import json
from business_objects.User import *

with open('definitions.json') as data_file:
    data = json.load(data_file)

word_counter = Word.select().count()

for chapter in data['book']:
    chapter_index = chapter['index']
    chapter_name = chapter['name']
    Chapter.create(chapter_index=chapter_index, chapter_name=chapter_name)
    for word in chapter['words']:
        word_text = word['text']
        Word.create(word_index=word_counter, word=word_text, chapter_index=chapter_index)
        for definition in word['definitions']:
            definition_text = definition['text']
            Definition.create(
                word_index=word_counter,
                definition=definition_text,
                chapter_index=chapter_index
            )
        word_counter += 1
