import json
from business_objects.User import *


class_code = 'A1B2C3D4E5'

with open('definitions.json') as definitions_file:
    definitions_json = json.load(definitions_file)

with open('rewards.json') as rewards:
    rewards_json = json.load(rewards)

question_index = 0

for chapter in definitions_json['book']:
    chapter_index = chapter['index']
    chapter_name = chapter['name']
    Chapter.create(chapter_index=chapter_index, chapter_name=chapter_name)
    for question in chapter['questions']:
        question_text = question['question_text']
        McPrompt.create(index=question_index, text=question_text, chapter_index=chapter_index, type=1)
        for correct_answer in question['correct_answers']:
            McChoice.create(
                question_index=question_index,
                text=correct_answer,
                correct=True
            )
        for incorrect_answer in question['incorrect_answers']:
            McChoice.create(
                question_index=question_index,
                text=incorrect_answer,
                correct=False
            )
        question_index += 1

Classroom.create(
    class_code=class_code,
    current_chapter=4,
    number_dailies_allowed=3,
    max_multiplier=5,
    daily_exp_base=30,
    daily_point_value=10000,
    daily_number_of_questions=25,
    registration_open=1
)

for reward in rewards_json['rewards']:
    Reward.create(
        class_code=class_code,
        reward_name=reward['reward_name'],
        reward_description=reward['reward_description'],
        required_points=reward['required_points']
    )

