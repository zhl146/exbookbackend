from random import shuffle, randint
from peewee import fn

from config import *
from business_objects.Models import Definition as Definition
from business_objects.Models import Word as Word


class DefinitionQuestion:
    __word_index = None
    __question_text = None
    __answer_choices = None
    __chapter_index = None
    __question_type = None

    def make_definition_question(
            self,
            chapter_index,
            question_type=None,
            cumulative=False,
            ):
        # if no question type is requested, flip a coin to determine the question type
        self.__chapter_index = chapter_index
        if question_type not in [0, 1]:
            self.__question_type = randint(0, 1)
        else:
            self.__question_type = question_type

        if cumulative:
            chapter_index = randint(1, chapter_index)

        query = (Word
                 .select()
                 .where(Word.chapter_index == chapter_index)
                 .order_by(fn.Rand())
                 .limit(number_of_multiple_choices)
                 )

        if self.__question_type == 1:

            definition_list = []
            for word in query:
                raw_definition = (Definition
                                  .select()
                                  .where(Definition.word_index == word.get_question_index)
                                  .order_by(fn.Rand())
                                  .limit(1)
                                  )[0]
                definition = {
                    "text": raw_definition.definition,
                    "index": word.get_question_index
                }
                definition_list.append(definition)

            self.__answer_choices = definition_list
            self.__question_text = query[0].word

        # question type 0 is definition prompt with word choices
        elif self.__question_type == 0:

            word_list = []
            for element in query:
                word = {
                    "text": element.word,
                    "index": element.get_question_index
                }
                word_list.append(word)

            raw_definition = (Definition
                              .select()
                              .where(Definition.word_index == query[0].get_question_index)
                              .order_by(fn.Rand())
                              .limit(1)
                              )[0]

            self.__answer_choices = word_list
            self.__question_text = raw_definition.definition

        self.__word_index = query[0].get_question_index
        shuffle(self.__answer_choices)


        return self

    def get_json_min(self):
        return {
            "prompt": self.__question_text,
            "answers": self.__answer_choices,
            "chapter_index": self.__chapter_index,
            "question_type": self.__question_type
        }

    def word_index(self):
        return self.__word_index

    def question_text(self):
        return self.__question_text

    def answer_choices(self):
        return self.__answer_choices

    def chapter_index(self):
        return self.__chapter_index

    def question_type(self):
        return self.__question_type

def unit_test():
    print("Starting unit test")
    Test_Result = True
    definition_question = MultipleChoiceQuestion()
    test_question_1 = definition_question.make_definition_question(
        1,
        question_type=2
    )
    jsonified_text = test_question_1.get_json_min()
    test_result = valid_json_object(jsonified_text)
    if not test_result:
        print("Unit test part 1 failed, generic random question failed")
        Test_Result = False

    test_question_2 = definition_question.make_definition_question(
        1,
        question_type=0
    )
    jsonified_text = test_question_2.get_json_min()
    test_result = valid_json_object(jsonified_text)
    if not test_result:
        print("Unit test part 2 failed, generic question type 0 failed")
        Test_Result = False

    test_question_3 = definition_question.make_definition_question(
        1,
        question_type=1
    )
    jsonified_text = test_question_3.get_json_min()
    test_result = valid_json_object(jsonified_text)
    if not test_result:
        print("Unit test part 2 failed, generic question type 1 failed")
        Test_Result = False

    test_question_4 = definition_question.make_definition_question(
        1,
        question_type=2,
        cumulative=True
    )
    jsonified_text = test_question_4.get_json_min()
    test_result = valid_json_object(jsonified_text)
    if not test_result:
        print("Unit test part 1 failed, generic random question failed")
        Test_Result = False

    test_question_5 = definition_question.make_definition_question(
        1,
        question_type=0,
        cumulative=True
    )
    jsonified_text = test_question_5.get_json_min()
    test_result = valid_json_object(jsonified_text)
    if not test_result:
        print("Unit test part 2 failed, generic question type 0 failed")
        Test_Result = False

    test_question_6 = definition_question.make_definition_question(
        1,
        question_type=1,
        cumulative=True
    )
    jsonified_text = test_question_6.get_json_min()
    test_result = valid_json_object(jsonified_text)
    if not test_result:
        print("Unit test part 2 failed, generic question type 1 failed")
        Test_Result = False

    if Test_Result:
        print("SUCCESS: Unit test for Definition Question complete")


def valid_json_object(json_object):
    assert json_object["prompt"]
    assert json_object["answers"]
    assert json_object["chapter_index"]
    assert json_object["question_type"] is not None
    return True

if __name__ == "__main__":
    unit_test()
