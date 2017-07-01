import datetime
import requests
from user_agents import parse

from business_objects.Models import *
from business_objects.User import User

import config as config

#########################################################################################
# DESCRIPTION
# checks the access token that is passed from the client against google database
# the access token is passed under the "user_identifier" label
# the google database should return information about the user including a user ID number
#
# RETURN CASES
# if the user id is returned, then we return all user information
# if the user is not a valid google user, then we return false
#
# TAKES
# "client_request" JSON that includes "user_identifier" field
#
# RETURNS
# user information json
# False bool
#########################################################################################


def get_token_info(client_request):
    try:
        token = client_request.headers.get('authorization').replace("Bearer ", "", 1)
        # print(token)

        auth0_endpoint = "https://zhl146.auth0.com/tokeninfo"

        response = (requests.post(auth0_endpoint, data={'id_token': token})).json()

        # print(response)
        return response

    except Exception as ex:
        print(ex)


def authenticate_user(client_request):
    user_information = get_token_info(client_request)
    if user_information:
        # print(user_information)
        user_id = str(user_information['identities'][0]['user_id'])
        user = User.get(User.user_id == user_id)
        if user:
            return user
        else:
            return False

#########################################################################################
# DESCRIPTION
#
#
# RETURN CASES
#
#
# TAKES
#
#
# RETURNS
#
#########################################################################################


def get_quest_options():
    chapter_list = []
    for chapter in Chapter.select():
        chapter_list.append(chapter.get_json_min())
    return {
        'chapter_options': chapter_list,
        'number_of_questions_options': config.number_of_question_options
    }

#########################################################################################
# DESCRIPTION
#
#
# RETURN CASES
#
#
# TAKES
#
#
# RETURNS
#
#########################################################################################


def make_activity_log_entry(user, correct, request):
    try:
        # ip_address = request.remote_addr
        # request_json = request.json
        user_agent = parse(request.user_agent.string)
        if user_agent.is_mobile:
            device_type = 0
        elif user_agent.is_tablet:
            device_type = 1
        elif user_agent.is_pc:
            device_type = 2
        else:
            device_type = -1

        new_activity_log_entry = ActivityLogEntry(
            correct=correct,
            question_index=user.current_question_index,
            answer_index=user.current_answer_index,
            datetime=datetime.datetime.now(),
            datetime_quest_started=user.datetime_quest_started,
            datetime_question_started=user.datetime_question_started,
            device_family=user_agent.device.family,
            device_model=user_agent.device.model,
            device_type=device_type,
            # ip_address=ip_address,
            is_daily=user.is_on_daily,
            is_timed=user.is_timed,
            # latitude=request_json['latitude'],
            # longitude=request_json['longitude'],
            number_of_questions=user.number_of_questions,
            user_id=user.user_id
        )
        new_activity_log_entry.save()
    except Exception as ex:
        print(ex)
        print("failed too make activity log entry.")

#########################################################################################
# DESCRIPTION
#
#
# RETURN CASES
#
#
# TAKES
#
#
# RETURNS
#
#########################################################################################


def make_quest_log_entry(user, request):
    try:
        # ip_address = request.remote_addr
        # request_json = request.json
        user_agent = parse(request.user_agent.string)
        if user_agent.is_mobile:
            device_type = 0
        elif user_agent.is_tablet:
            device_type = 1
        elif user_agent.is_pc:
            device_type = 2
        else:
            device_type = -1

        new_quest_log_entry = QuestLogEntry(
            chapter_index=user.chapter_index_id,
            cumulative=user.cumulative,
            datetime_quest_completed=datetime.datetime.now(),
            datetime_quest_started=user.datetime_quest_started,
            device_family=user_agent.device.family,
            device_model=user_agent.device.model,
            device_type=device_type,
            # ip_address=ip_address,
            is_daily=user.is_on_daily,
            is_timed=user.is_timed,
            # latitude=request_json['latitude'],
            # longitude=request_json['longitude'],
            number_of_questions=user.number_of_questions,
            user_id=user.user_id,
            number_correct=user.number_correct
        )
        new_quest_log_entry.save()
    except Exception as ex:
        print(ex)
        print("Failed to make quest log entry.")

#########################################################################################
# DESCRIPTION
#
#
# RETURN CASES
#
#
# TAKES
#
#
# RETURNS
#
#########################################################################################


def get_rewards(user):
    class_code = user.class_code_id
    reward_list = []
    for reward in Reward.select().where(Reward.class_code == class_code):
        reward_list.append(reward.get_json_min())

    return reward_list

#########################################################################################
# DESCRIPTION
#
#
# RETURN CASES
#
#
# TAKES
#
#
# RETURNS
#
#########################################################################################


def get_daily_info(user):
    day_start = datetime.datetime.today().replace(hour=0, minute=0, second=0, microsecond=0)
    day_end = day_start.replace(hour=23, minute=59, second=59)

    class_code = user.class_code_id
    classroom = Classroom.get(Classroom.class_code == class_code)
    dailies_complete = (
        QuestLogEntry.select()
        .where(
            QuestLogEntry.user_id == user.user_id,
            QuestLogEntry.is_daily == True,
            QuestLogEntry.datetime_quest_completed.between(day_start, day_end)
        )
        .count()
    )
    dailies_allowed = classroom.number_dailies_allowed
    current_chapter = classroom.current_chapter_id
    return {
        'dailies_complete': dailies_complete,
        'dailies_allowed': dailies_allowed,
        'daily_chapter': current_chapter
    }


#########################################################################################
# DESCRIPTION
#
#
# RETURN CASES
#
#
# TAKES
#
#
# RETURNS
#
#########################################################################################

def get_leader_board(user):
    leader_board = []
    class_code = user.class_code_id

    all_users = User.select(User.class_code == class_code).order_by(-User.total_points)
    for single_user in all_users:
        leader_board.append(single_user.total_points)

    return leader_board

#########################################################################################
# DESCRIPTION
#
#
# RETURN CASES
#
#
# TAKES
#
#
# RETURNS
#
#########################################################################################


def record_location(request, action):
    request_json = request.json
    Location.create(
        latitude=request_json['latitude'],
        longitude=request_json['longitude'],
        action=action
    )

#########################################################################################
# DESCRIPTION
#
#
# RETURN CASES
#
#
# TAKES
#
#
# RETURNS
#
#########################################################################################


def record_answer_choice(answer_index):
    chosen_answer = McChoice.get(McChoice.index == answer_index)
    chosen_answer.times_chosen += 1
    chosen_answer.save()
