import datetime
import math

from business_objects.Models import *
from business_objects.questions.MultipleChoiceQuestion import MultipleChoiceQuestion


class User(BaseModel):
    chapter_index = ForeignKeyField(db_column='chapter_index', null=True, rel_model=Chapter, to_field='chapter_index')
    class_code = ForeignKeyField(db_column='class_code', null=True, rel_model=Classroom, to_field='class_code')
    completion_points = IntegerField(null=True)
    cumulative = IntegerField(null=True)
    current_progress = IntegerField(null=True)
    current_answer_index = IntegerField(null=True)
    current_question_index = IntegerField(null=True)
    datetime_quest_started = DateTimeField(null=True)
    datetime_question_started = DateTimeField(null=True)
    e_mail = CharField()
    first_name = CharField(null=True)
    is_on_daily = IntegerField(null=True)
    is_timed = IntegerField(null=True)
    last_name = CharField(null=True)
    multiplier = IntegerField(null=True)
    number_correct = IntegerField(null=True)
    number_of_questions = IntegerField(null=True)
    points_earned_current_quest = IntegerField(null=True)
    points_per_question = IntegerField(null=True)
    question_type = IntegerField(null=True)
    reward_level = IntegerField()
    total_points = IntegerField(null=True)
    user_id = CharField(db_column='user_id', primary_key=True)
    user_role = IntegerField()
    research_agreement_status = IntegerField()

    def get_json_min(self):
        data = self._data

        key_list = (
            'class_code',
            'current_answer_index',
            'datetime_quest_started',
            'datetime_question_started',
            'e_mail',
            'user_role'
        )

        for key in key_list:
            data.pop(key, None)

        return data

    class Meta:
        db_table = 'users'

    #########################################################################################
    # Convenience Methods
    #########################################################################################

    def sign_agreement(self, agreement_choice):
        self.research_agreement_status = agreement_choice

    def start_new_quest(self, request, user_classroom):
        client_choices = request.json
        is_daily = client_choices['is_daily']
        if is_daily:
            self.__start_daily(user_classroom)
        else:
            self.__start_practice(client_choices)

    def start_new_question(self):
        new_question = self.__generate_new_question()
        self.current_answer_index = new_question.get_correct_answer_index()
        self.current_question_index = new_question.get_question_index()
        self.datetime_question_started = datetime.datetime.now()

        return new_question

    def drop_user_quest(self):
        self.chapter_index = None
        self.completion_points = None
        self.cumulative = None
        self.current_progress = 0
        self.current_answer_index = None
        self.current_question_index = None
        self.datetime_question_started = None
        self.datetime_quest_started = None
        self.is_on_daily = None
        self.is_timed = None
        self.multiplier = 1
        self.number_correct = 0
        self.number_of_questions = None
        self.points_earned_current_quest = 0
        self.points_per_question = None
        self.question_type = None

    def update_quest_progress(self):
        self.current_progress += 1

    def award_question_points(self, user_classroom):
        points_earned = self.points_per_question*self.multiplier
        self.points_earned_current_quest += points_earned
        self.total_points += points_earned
        self.number_correct += 1
        self.__increment_multiplier(user_classroom)

    def award_daily_rewards(self, user_classroom):

        base = user_classroom.daily_exp_base
        percentage_correct = self.number_correct/self.number_of_questions
        points_earned = int(round(math.pow(base, percentage_correct)/base*self.completion_points))
        self.completion_points = points_earned
        self.total_points += points_earned

    def calculate_user_performance(self):
        user_performance = {
            "number_correct": self.number_correct,
            "number_total": self.number_of_questions,
            "points_per_question": self.points_per_question,
            "multiplier_points": self.points_earned_current_quest - self.points_per_question*self.number_correct,
            "score_bonus": self.completion_points
        }
        return user_performance

    def is_eligible_for_daily(self, user_classroom):
        day_start = datetime.datetime.today().replace(hour=0, minute=0, second=0, microsecond=0)
        day_end = day_start.replace(hour=23, minute=59, second=59)
        dailies_complete = (
            QuestLogEntry.select()
            .where(
                QuestLogEntry.user_id == self.user_id,
                QuestLogEntry.is_daily == True,
                QuestLogEntry.datetime_quest_completed.between(day_start, day_end)
            )
            .count()
        )
        dailies_allowed = user_classroom.number_dailies_allowed

        return dailies_allowed >= dailies_complete

    def get_classroom(self):
        return Classroom.get(Classroom.class_code == self.class_code)

    #########################################################################################
    # Private Methods
    #########################################################################################

    def __increment_multiplier(self, user_classroom):
        if self.multiplier < user_classroom.max_multiplier:
            self.multiplier += 1

    def __generate_new_question(self):
        new_question = MultipleChoiceQuestion().make_multiple_choice(
            chapter_index=self.chapter_index_id,
            cumulative=self.cumulative,
            question_type=1
        )

        return new_question

    def __start_daily(self, user_classroom):

        self.datetime_quest_started = datetime.datetime.now()
        # peewee requires the use of _id in order to access a foreign key value
        self.chapter_index = user_classroom.current_chapter_id
        # if you do not use _id, then it will access the foreign object itself
        self.current_progress = 0
        self.number_correct = 0
        self.completion_points = user_classroom.daily_point_value
        self.is_timed = True
        self.points_per_question = 20
        self.number_of_questions = user_classroom.daily_number_of_questions
        self.cumulative = True
        self.question_type = 3
        self.is_on_daily = True
        self.points_earned_current_quest = 0

    def __start_practice(self, client_choices):
        chapter_index = client_choices['chapter_index']
        is_timed = client_choices['is_timed']
        number_of_questions = client_choices['number_of_questions']
        cumulative = client_choices['cumulative']
        question_type = client_choices['question_type']

        points_per_question = 10
        if is_timed:
            points_per_question += 3
        if cumulative:
            points_per_question += 3
        if question_type == 3:
            points_per_question += 3

        self.datetime_quest_started = datetime.datetime.now()
        self.chapter_index = chapter_index
        self.current_progress = 0
        self.number_correct = 0
        self.completion_points = 0
        self.is_timed = is_timed
        self.points_per_question = points_per_question
        self.number_of_questions = number_of_questions
        self.cumulative = cumulative
        self.question_type = question_type
        self.is_on_daily = False
        self.points_earned_current_quest = 0
