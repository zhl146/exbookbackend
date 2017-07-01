from random import shuffle, randint
from peewee import fn

from config import *
from business_objects.Models import McPrompt as Prompt
from business_objects.Models import McChoice as Choice


class MultipleChoiceQuestion:
    __question_index = None
    __question_text = None
    __answer_choices = []
    __chapter_index = None
    __correct_choice_index = None

    def make_multiple_choice(
            self,
            chapter_index,
            cumulative=False,
            question_type=0
    ):
        self.__chapter_index = chapter_index
        self.__answer_choices = []
        if cumulative:
            if randint(0, 1) == 0:
                chapter_index = randint(1, chapter_index)

        question = (Prompt
                    .select()
                    .where(Prompt.chapter_index == chapter_index,
                           Prompt.type == question_type)
                    .order_by(fn.Rand())
                    .get()
                    )

        self.__question_index = question.get_index()
        self.__question_text = question.get_prompt_text()

        correct_choice = Choice.get(Choice.question_index == question, Choice.correct == True)
        self.__answer_choices.append(correct_choice.get_json_min())
        self.__correct_choice_index = correct_choice.get_index()

        incorrect_choices = (Choice
                             .select()
                             .where(Choice.question_index == question, Choice.correct == False)
                             .order_by(fn.Rand())
                             .limit(number_of_multiple_choices-1)
                             )

        for incorrect_choice in incorrect_choices:
            self.__answer_choices.append(incorrect_choice.get_json_min())

        shuffle(self.__answer_choices)

        return self

    def get_json_min(self):
        return {
            "prompt": self.__question_text,
            "answers": self.__answer_choices,
            "chapter_index": self.__chapter_index
        }

    def get_question_index(self):
        return self.__question_index

    def question_text(self):
        return self.__question_text

    def answer_choices(self):
        return self.__answer_choices

    def get_correct_answer_index(self):
        return self.__correct_choice_index

#
# def unit_test():
#     print("Starting unit test")
#     Test_Result = True
#     definition_question = MultipleChoiceQuestion()
#     test_question_1 = definition_question.make_multiple_choice(
#         1,
#     )
#     jsonified_text = test_question_1.get_json_min()
#     test_result = valid_json_object(jsonified_text)
#     if not test_result:
#         print("Unit test part 1 failed, generic random question failed")
#         Test_Result = False
#
#     test_question_2 = definition_question.make_multiple_choice(
#         1,
#         question_type=0
#     )
#     jsonified_text = test_question_2.get_json_min()
#     test_result = valid_json_object(jsonified_text)
#     if not test_result:
#         print("Unit test part 2 failed, generic question type 0 failed")
#         Test_Result = False
#
#     test_question_3 = definition_question.make_definition_question(
#         1,
#         question_type=1
#     )
#     jsonified_text = test_question_3.get_json_min()
#     test_result = valid_json_object(jsonified_text)
#     if not test_result:
#         print("Unit test part 2 failed, generic question type 1 failed")
#         Test_Result = False
#
#     test_question_4 = definition_question.make_definition_question(
#         1,
#         question_type=2,
#         cumulative=True
#     )
#     jsonified_text = test_question_4.get_json_min()
#     test_result = valid_json_object(jsonified_text)
#     if not test_result:
#         print("Unit test part 1 failed, generic random question failed")
#         Test_Result = False
#
#     test_question_5 = definition_question.make_definition_question(
#         1,
#         question_type=0,
#         cumulative=True
#     )
#     jsonified_text = test_question_5.get_json_min()
#     test_result = valid_json_object(jsonified_text)
#     if not test_result:
#         print("Unit test part 2 failed, generic question type 0 failed")
#         Test_Result = False
#
#     test_question_6 = definition_question.make_definition_question(
#         1,
#         question_type=1,
#         cumulative=True
#     )
#     jsonified_text = test_question_6.get_json_min()
#     test_result = valid_json_object(jsonified_text)
#     if not test_result:
#         print("Unit test part 2 failed, generic question type 1 failed")
#         Test_Result = False
#
#     if Test_Result:
#         print("SUCCESS: Unit test for Definition Question complete")
#
#
# def valid_json_object(json_object):
#     assert json_object["prompt"]
#     assert json_object["answers"]
#     assert json_object["chapter_index"]
#     assert json_object["question_type"] is not None
#     return True
#
# if __name__ == "__main__":
#     unit_test()
