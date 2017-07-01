import logging
from logging.handlers import RotatingFileHandler
from rest_functions import *
from config import *
from flask import Flask, jsonify, request, abort, _request_ctx_stack

import jwt
import base64
from functools import wraps
from werkzeug.local import LocalProxy

app = Flask(__name__, static_url_path='/')


# Authentication annotation
current_user = LocalProxy(lambda: _request_ctx_stack.top.current_user)


# Authentication attribute/annotation
def authenticate(error):
    resp = jsonify(error)

    resp.status_code = 500

    return resp


def requires_auth(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        auth = request.headers.get('Authorization', None)
        if not auth:
            return authenticate({'code': 'authorization_header_missing', 'description': 'Authorization header is expected'})

        parts = auth.split()

        if parts[0].lower() != 'bearer':
            return {'code': 'invalid_header', 'description': 'Authorization header must start with Bearer'}
        elif len(parts) == 1:
            return {'code': 'invalid_header', 'description': 'Token not found'}
        elif len(parts) > 2:
            return {'code': 'invalid_header', 'description': 'Authorization header must be Bearer + \s + token'}

        token = parts[1]
        try:
            payload = jwt.decode(
                token,
                base64.b64decode('Ruhcmld2nOTwFL4u_NZgUd8Dzj-LhZVEw5o4deIqcy7O_A6LQ4jJhtvKgy6jauN4'.replace("_","/").replace("-","+")),
                audience='p0YHk3HYjJP7HjleA1zwvNS9xCb5WfIw',
                options={'verify_iat': False}
            )
        except jwt.ExpiredSignature:
            return authenticate({
                'code': 'token_expired',
                'description': 'token is expired'
            })
        except jwt.InvalidAudienceError:
            return authenticate({
                'code': 'invalid_audience',
                'description': 'incorrect audience, expected: p0YHk3HYjJP7HjleA1zwvNS9xCb5WfIw'
            })
        except jwt.DecodeError:
            return authenticate({
                'code': 'token_invalid_signature',
                'description': 'token signature is invalid'
            })
        except Exception as ex:
            app.logger.error(" Unhandled Exception in authentication method: {}").format(str(ex))
            return authenticate({'code': 'unhandled exception', 'description': 'See logs for details, unhandled exception'})
        _request_ctx_stack.top.current_user = payload
        return f(*args, **kwargs)

    return decorated


@app.before_request
def before_request():
    print('Request Incoming')
    database.connect()


@app.after_request
def after_request(response):
    # TODO: check to see if this CORS implementation is safe
    # TODO: Mobile may not need CORS here - check to see if it is okay without it
    response.headers.add('Access-Control-Allow-Origin', '*')
    response.headers.add('Access-Control-Allow-Headers', 'Content-Type,Authorization')
    response.headers.add('Access-Control-Allow-Methods', 'GET,PUT,POST,DELETE')
    return response


@app.teardown_request
def _db_close(exc):
    if not database.is_closed():
        database.close()

# -------------------------------------------------------------
# Routes
# -------------------------------------------------------------

# -------------------------------------------------------------
# Student client routes
# -------------------------------------------------------------

#########################################################################################
# DESCRIPTION
# returns the user's information to the client after authenticating
#
# RETURN CASES
# should always return user json
#
# TAKES
# user authentication token
#
# RETURNS
# user json
#
#########################################################################################


@app.route('/api/v1/status/get', methods=['POST'])
@requires_auth
def route_get_status():
    try:
        app.logger.info(request.json)
        user = authenticate_user(request)
        try:
            daily_info = get_daily_info(user)
            rewards = get_rewards(user)
            quest_options = get_quest_options()

            return jsonify({
                "user": user.get_json_min(),
                "daily_status": daily_info,
                'rewards': rewards,
                "quest_options": quest_options
            })
        except Exception as ex:
            app.logger.error("Something went wrong, error: ")
            app.logger.error(ex)
            return abort(500, "Error. If this error persists, please contact an admin")
    except Exception as ex:
        app.logger.error("Something went wrong, error: ")
        app.logger.error(ex)
        return abort(500, "Error. If this error persists, please contact an admin")

#########################################################################################
# DESCRIPTION
# When the user requests, authenticate them and then serves up a new question
# for the start of the quest
#
# RETURN CASES
# Error: if the user does not authenticate
# Error: if the user causes an internal server error
# On Success: Returns the user object and a new question in json format
#
# TAKES
# user authentication token string, chapter_index int, number_of_questions int,
# is_timed boolean, cumulative boolean
#
# RETURNS
# updated user object, new question, and 200 code
#
#########################################################################################


@app.route('/api/v1/quest/start', methods=['POST'])
@requires_auth
def route_start_quest():
    try:
        incoming_request = request
        app.logger.info(incoming_request)
        # check authentication
        user = authenticate_user(request)
        if user:
            user_classroom = Classroom.get(Classroom.class_code == user.class_code)
            user.start_new_quest(request, user_classroom)
            new_question = user.start_new_question()
            user.save()

            return jsonify({
                "question": new_question.get_json_min(),
                "user": user.get_json_min()
            })
        else:
            return abort(403, "Unable to authenticate user")

    except Exception as ex:
        app.logger.error("Something went wrong, error: ")
        app.logger.error(ex)
        return abort(500, "Error. If this error persists, please contact an admin")

#########################################################################################
# DESCRIPTION
# When the user requests, returns a valid set of quest options
# to populate the quest selection screen
#
# RETURN CASES
# Error: if the user does not authenticate
# Error: if the user causes an internal server error
# On Success: Returns the user object and a new set of question parameters
#
# TAKES
# user authentication token string
#
# RETURNS
# json including user and valid quest parameters
#
#########################################################################################


@app.route('/api/v1/quests/get', methods=['POST'])
@requires_auth
def route_get_quests():
    try:
        incoming_request = request
        app.logger.info(incoming_request)
        # check authentication
        user = authenticate_user(request)
        if user:
            quest_options = get_quest_options()
            return jsonify({
                "user": user.get_json_min(),
                "quest_options": quest_options
            })
        else:
            return abort(403, "Unable to authenticate user")

    except Exception as ex:
        app.logger.error("Something went wrong, error: ")
        app.logger.error(ex)
        return abort(500, "Error. If this error persists, please contact an admin")

#########################################################################################
# DESCRIPTION
# Drops the users current quest, presumably used before start new quest if user is frustrated
#
# RETURN CASES
# Error: if the user does not authenticate
# Error: if the user causes an internal server error
# On Success: Returns the user object and a new question in json format
#
# TAKES
# user authentication token string
#
# RETURNS
# updated user object, and 200 code
#
#########################################################################################


@app.route('/api/v1/quest/drop', methods=['POST'])
@requires_auth
def route_drop_quest():
    try:
        incoming_request = request
        app.logger.info(incoming_request)
        # check authentication
        user = authenticate_user(request)
        if user:
            user.drop_user_quest()
            user.save()

            return jsonify({
                "user": user.get_json_min()
            })

        else:
            return abort(403, "Unable to authenticate user")

    except Exception as ex:
        app.logger.error("Something went wrong, error: ")
        app.logger.error(ex)
        return abort(500, "Error. If this error persists, please contact an admin")


#########################################################################################
# DESCRIPTION
# Assumed use: on user phone reboot or other session clear, the user will request a new
# question.  This could be used to avoid particularly hard questions, watch logs for abuse
#
# RETURN CASES
# Error: if the user does not authenticate
# Error: if the user causes an internal server error
# On Success: Returns the user object and a new question in json format
#
# TAKES
# user authentication token string
#
# RETURNS
# updated user object, new question, and 200 code
#
#########################################################################################


@app.route('/api/v1/quest/resume', methods=['POST'])
@requires_auth
def route_resume_quest():
    try:
        incoming_request = request
        app.logger.info(incoming_request)

        # check authentication
        user = authenticate_user(request)
        if user:
            new_question = user.start_new_question()
            user.save()

            return jsonify({
                'user': user.get_json_min(),
                'question': new_question.get_json_min()
            })
        else:
            return abort(403, "Unable to authenticate user")

    except Exception as ex:
        app.logger.error("Something went wrong, error: ")
        app.logger.error(ex)
        return abort(500, "Error. If this error persists, please contact an admin")

#########################################################################################
# DESCRIPTION
# User is submitting answer for a question they were presented
#
# RETURN CASES
# Error: if the user does not authenticate
# Error: if the user causes an internal server error
# On Success: returns updated user object, if they got the answer correct (boolean), the index of the correct answer,
# quest_complete boolean flag, and a new question for them to answer if they are still in an active quest
#
# TAKES
# user authentication token string, user_answer
# TODO: geo location data
# RETURNS
# user object, answer_index (int), correct (boolean), question object, quest_complete (boolean)
#########################################################################################


@app.route('/api/v1/question/submit', methods=['POST'])
@requires_auth
def route_submit_question():
    try:
        app.logger.info(request.json)

        user = authenticate_user(request)
        if user:
            quest_complete = (user.current_progress >= user.number_of_questions)

            if quest_complete:
                return jsonify({
                    "user": user.get_json_min(),
                    "quest_complete": True
                })

            user_classroom = Classroom.get(Classroom.class_code == user.class_code)

            correct_answer = user.current_answer_index

            if request.json['user_answer']:
                user_answer = request.json['user_answer']
                correct = (user_answer == correct_answer)
                record_answer_choice(user_answer)
            else:
                correct = False
                user_answer = None

            if correct:
                user.award_question_points(user_classroom)
            else:
                user.multiplier = 1
            record_location(request, 1)
            make_activity_log_entry(user, correct, request)
            user.update_quest_progress()

            quest_complete = (user.current_progress >= user.number_of_questions)

            if quest_complete:
                record_location(request, 0)
                make_quest_log_entry(user, request)
                if user.is_on_daily and user.is_eligible_for_daily(user_classroom):
                    user.award_daily_rewards(user_classroom)
                user_performance = user.calculate_user_performance()
                user.drop_user_quest()
                user.save()
                daily_info = get_daily_info(user)

                return jsonify({
                    "user": user.get_json_min(),
                    "feedback": {
                        "is_correct": correct,
                        "correct_answer": correct_answer,
                        "user_answer": user_answer
                    },
                    "quest_complete": quest_complete,
                    "user_performance": user_performance,
                    "daily_status": daily_info
                })

            else:
                new_question = user.start_new_question()
                user.save()

                return jsonify({
                    "user": user.get_json_min(),
                    "feedback": {
                        "is_correct": correct,
                        "correct_answer": correct_answer,
                        "user_answer": user_answer
                    },
                    "question": new_question.get_json_min(),
                    "quest_complete": quest_complete
                })
        else:
            return abort(403, "Unable to authenticate user")

    except Exception as ex:
        app.logger.error("Something went wrong, error: ")
        app.logger.error(ex)
        return abort(500, "Error. If this error persists, please contact an admin")

#########################################################################################
# DESCRIPTION
# new user is submitting for an account
#
# RETURN CASES
# Error: if the user does not authenticate
# Error: if the user causes an internal server error
# On Success:
#
# TAKES
# user_identifier, sub, email, first name, last name
#
# RETURNS
# user_exists (boolean), created (boolean), error flag if we think an error occured but couldnt find it
#########################################################################################


@app.route('/api/v1/account/create', methods=['POST'])
@requires_auth
def route_create_account():
    try:
        incoming_request = request
        app.logger.info(incoming_request)

        user_information = get_token_info(request)
        if user_information:
            app.logger.info(user_information)
            user_id = str(user_information['identities'][0]['user_id'])

            if User.select().where(User.user_id == user_id).count():
                print('aborting')
                return abort(500, "Error: user already exists.")
            class_code = request.json['class_code']
            user_first_name = user_information['given_name']
            user_last_name = user_information['family_name']
            user_email = user_information['email']

            app.logger.info('Creating new user account')
            new_user = User.create(
                user_id=user_id,
                first_name=user_first_name,
                last_name=user_last_name,
                e_mail=user_email,
                class_code=class_code,
                total_points=0,
                reward_level=0,
                multiplier=1,
                user_role=0
            )

            if new_user:
                daily_info = get_daily_info(new_user)
                rewards = get_rewards(new_user)
                quest_options = get_quest_options()

                return jsonify({
                    "user": new_user.get_json_min(),
                    "daily_status": daily_info,
                    'rewards': rewards,
                    "quest_options": quest_options
                })

    except Exception as ex:
        app.logger.error("Something went wrong, error: ")
        app.logger.error(ex)
        return abort(500, "Error. If this error persists, please contact an admin")

#########################################################################################
# DESCRIPTION
#
#
# RETURN CASES
#
#
#
#
# TAKES
#
#
# RETURNS
#
#########################################################################################


@app.route('/api/v1/daily/get', methods=['POST'])
@requires_auth
def route_get_daily():
    try:
        app.logger.info(request.json)

        user = authenticate_user(request)
        if user:
            daily_info = get_daily_info(user)

            return jsonify({
                'daily_status': daily_info
            })
        else:
            return abort(403, "Unable to authenticate user")

    except Exception as ex:
        app.logger.error("Something went wrong, error: ")
        app.logger.error(ex)
        return abort(500, "Error. If this error persists, please contact an admin")

#########################################################################################
# DESCRIPTION
#
#
# RETURN CASES
#
#
#
#
# TAKES
#
#
# RETURNS
#
#########################################################################################


@app.route('/api/v1/agreement/sign', methods=['POST'])
@requires_auth
def route_sign_agreement():
    try:
        app.logger.info(request.json)
        choice = request.json['agreement_choice']
        user = authenticate_user(request)
        if user:
            user.sign_agreement(choice)
            user.save()

            return jsonify({
                'user': user.get_json_min()
            })
        else:
            return abort(403, "Unable to authenticate user")

    except Exception as ex:
        app.logger.error("Something went wrong, error: ")
        app.logger.error(ex)
        return abort(500, "Error. If this error persists, please contact an admin")


# -------------------------------------------------------------
# Professor client routes
# -------------------------------------------------------------

#########################################################################################
# DESCRIPTION
#
#
# RETURN CASES
#
#
#
#
# TAKES
#
#
# RETURNS
#
#########################################################################################


@app.route('/api/v1/current_chapter/set', methods=['POST'])
@requires_auth
def route_set_chapter():
    try:
        app.logger.info(request.json)
        client_request = request.json

        user = authenticate_user(request)
        user_classroom = Classroom.get(Classroom.class_code == user.class_code)

        user_classroom.current_chapter = client_request['chapter_index']

        user_classroom.save()

    except Exception as ex:
        app.logger.error("Something went wrong, error: ")
        app.logger.error(ex)
        return abort(500, "Error. If this error persists, please contact an admin")

#########################################################################################
# DESCRIPTION
#
#
# RETURN CASES
#
#
#
#
# TAKES
#
#
# RETURNS
#
#########################################################################################

#########################################################################################
# DESCRIPTION
#
#
# RETURN CASES
#
#
#
#
# TAKES
#
#
# RETURNS
#
#########################################################################################

#########################################################################################
# DESCRIPTION
#
#
# RETURN CASES
#
#
#
#
# TAKES
#
#
# RETURNS
#
#########################################################################################

#########################################################################################
# DESCRIPTION
#
#
# RETURN CASES
#
#
#
#
# TAKES
#
#
# RETURNS
#
#########################################################################################

#########################################################################################
# DESCRIPTION
#
#
# RETURN CASES
#
#
#
#
# TAKES
#
#
# RETURNS
#
#########################################################################################

# -------------------------------------------------------------
# Runs the actual server
# -------------------------------------------------------------


def start_logging():
    handler = RotatingFileHandler('/var/log/exbook/exbook.log', maxBytes=100000, backupCount=10)
    handler.setLevel(logging.DEBUG)
    handler.setFormatter(logging.Formatter(
        '%(asctime)s %(levelname)s: %(message)s '
        '[in %(pathname)s:%(lineno)d]'
    ))
    app.logger.addHandler(handler)
    app.config['PROPAGATE_EXCEPTIONS'] = True


def start_flask():
    start_logging()
    app.debug = True
    app.logger.info('server started locally')
    app.run(host='localhost', port=5000)

if __name__ == "__main__":
    start_flask()
