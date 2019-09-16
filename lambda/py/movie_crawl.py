# -*- coding: utf-8 -*-

# This is a simple Hello World Alexa Skill, built using
# the implementation of handler classes approach in skill builder.
import logging
import requests
import random

from ask_sdk_core.skill_builder import SkillBuilder
from ask_sdk_core.dispatch_components import AbstractRequestHandler
from ask_sdk_core.dispatch_components import AbstractExceptionHandler
from ask_sdk_core.utils import is_request_type, is_intent_name
from ask_sdk_core.handler_input import HandlerInput

from ask_sdk_model.ui import SimpleCard
from ask_sdk_model import Response

sb = SkillBuilder()

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

indent_slots = {
    'date_slot': 'date',
    'date_slot_key': 'DATE',
    'industry_slot': 'industry',
    'industry_slot_key': 'Industry',
}

class LaunchRequestHandler(AbstractRequestHandler):
    """Handler for Skill Launch."""
    def can_handle(self, handler_input):
        # type: (HandlerInput) -> bool
        return is_request_type("LaunchRequest")(handler_input)

    def handle(self, handler_input):
        # type: (HandlerInput) -> Response
        speech_text = "Welcome to Movie Crawl, you can ask movie releases by saying, what's coming this week in Bollywood?"

        handler_input.response_builder.speak(speech_text).set_card(
            SimpleCard("Movie Crawl", speech_text)).set_should_end_session(
            False)
        return handler_input.response_builder.response


class HelpIntentHandler(AbstractRequestHandler):
    """Handler for Help Intent."""
    def can_handle(self, handler_input):
        # type: (HandlerInput) -> bool
        return is_intent_name("AMAZON.HelpIntent")(handler_input)

    def handle(self, handler_input):
        # type: (HandlerInput) -> Response
        speech_text = "You can ask about movie releases to me!!"

        handler_input.response_builder.speak(speech_text).ask(
            speech_text).set_card(SimpleCard(
                "Movie Help", speech_text))
        return handler_input.response_builder.response


class CancelOrStopIntentHandler(AbstractRequestHandler):
    """Single handler for Cancel and Stop Intent."""
    def can_handle(self, handler_input):
        # type: (HandlerInput) -> bool
        return (is_intent_name("AMAZON.CancelIntent")(handler_input) or
                is_intent_name("AMAZON.StopIntent")(handler_input))

    def handle(self, handler_input):
        # type: (HandlerInput) -> Response
        speech_text = "Goodbye!"

        handler_input.response_builder.speak(speech_text).set_card(
            SimpleCard("Movie Crawl", speech_text))
        return handler_input.response_builder.response


class FallbackIntentHandler(AbstractRequestHandler):
    """AMAZON.FallbackIntent is only available in en-US locale.
    This handler will not be triggered except in that locale,
    so it is safe to deploy on any locale.
    """
    def can_handle(self, handler_input):
        # type: (HandlerInput) -> bool
        return is_intent_name("AMAZON.FallbackIntent")(handler_input)

    def handle(self, handler_input):
        # type: (HandlerInput) -> Response
        speech_text = (
            "The Movie Crawl skill can't help you with that.  "
            "You can ask about movie releases by saying, movies releasing in Bollywood this friday!!")
        reprompt = "You can ask about movie releases by saying, movies releasing in Bollywood this friday!!"
        handler_input.response_builder.speak(speech_text).ask(reprompt)
        return handler_input.response_builder.response


class SessionEndedRequestHandler(AbstractRequestHandler):
    """Handler for Session End."""
    def can_handle(self, handler_input):
        # type: (HandlerInput) -> bool
        return is_request_type("SessionEndedRequest")(handler_input)

    def handle(self, handler_input):
        # type: (HandlerInput) -> Response
        return handler_input.response_builder.response


class CatchAllExceptionHandler(AbstractExceptionHandler):
    """Catch all exception handler, log exception and
    respond with custom message.
    """
    def can_handle(self, handler_input, exception):
        # type: (HandlerInput, Exception) -> bool
        return True

    def handle(self, handler_input, exception):
        # type: (HandlerInput, Exception) -> Response
        logger.error(exception, exc_info=True)

        speech = "Sorry, there was some problem. Please try again!!"
        handler_input.response_builder.speak(speech).ask(speech)

        return handler_input.response_builder.response


class GetUpcomingMoviesHandler(AbstractRequestHandler):
    """Handler for Get Upcoming Movies Intent """
    def can_handle(self, handler_input):
        # type: (HandlerInput) -> bool
        return is_intent_name("GetUpcomingMovies")(handler_input)

    def handle(self, handler_input):
        # type (HandlerInput) -> Response
        slots = handler_input.request_envelope.request.intent.slots

        if indent_slots['industry_slot'] in slots and slots[indent_slots['industry_slot']].value:
            industry_value = slots[indent_slots['industry_slot']].value
            
            request_url = "https://api.themoviedb.org/3/movie/upcoming"
            parameters = {
                'api_key': 'c0f06b953bd8a08dfaef7196d198b463',
            }

            region_dict = {
                "Bollywood": {
                    'region': "IN"
                },
                "Hollywood": {
                    'region': "US"
                }
            }

            if not industry_value:
                industry_value = random.choice(list(region_dict))
        
            parameters.update(region_dict[industry_value])
            
            response = requests.get(request_url, params=parameters).json()
            movies = []
            card_movies = []

            if len(response['results']):
                speech_text = "Upcoming movies in {} are:- ".format(industry_value)
                card_text = speech_text + '\n'

                for i, item in enumerate(response['results'][:5]):
                    movies.append(item['title'])
                    card_movies.append(str(i+1) + '. '+ item['title'])

                speech_text += ', '.join(movies).replace('&', 'and')
                card_text += '\n'.join(card_movies)

                if len(response['results']) > 5:
                    speech_text += ", and many more."
                    card_text += ", and many more."

            else:
                speech_text = "There are no upcoming movies."

            handler_input.response_builder.speak(speech_text).set_card(
                SimpleCard("Upcoming Movie Releases", card_text)).set_should_end_session(True)
        else:
            speech_text = "I am not sure."
            reprompt = "You can ask by saying, upcoming movies in Hollywood"
            handler_input.response_builder.speak(speech_text).ask(reprompt)

        return handler_input.response_builder.response


class GetMovieReleasesHandler(AbstractRequestHandler):
    """Handler for Get Movie Releases"""
    def can_handle(self, handler_input):
        return is_intent_name("GetMovieReleases")(handler_input)

    def handle(self, handler_input):

        def set_date_parameters(params, date_value):
            from datetime import datetime, timedelta

            date_list = date_value.split('-')
            date_list_len = len(date_list)
            date_year = date_list[0] 
            parameters['primary_release_year'] = date_year

            if 'W' in date_value: # user request for week range
                start_date = datetime.strptime(date_value + '-1', "%Y-W%W-%w")
                end_date = start_date + timedelta(days=6)
                params['primary_release_date.gte'] = start_date.strftime("%Y-%m-%d")
                params['primary_release_date.lte'] = end_date.strftime("%Y-%m-%d")

            elif date_list_len == 2 and 'W' not in date_value: # User request for month range
                start_date = datetime.strptime(date_value , "%Y-%m")
                next_month = start_date.replace(day=28) + timedelta(days=4)
                end_date = next_month - timedelta(days=next_month.day)
                params['primary_release_date.gte'] = start_date.strftime("%Y-%m-%d")
                params['primary_release_date.lte'] = end_date.strftime("%Y-%m-%d")

            # elif date_list_len == 1 and 'W' not in date_value: # User request for full year
                

            else: # It is a normal date
                params['primary_release_date.gte'] = params['primary_release_date.lte'] = date_value

        def set_industry_parameters(params, industry_value):
            industry_dict = {
                "Bollywood": {
                    'region': 'IN',
                    'with_original_language': 'hi'
                }, 
                "Hollywood": {
                    'region': 'US',
                    'sort_by': 'popularity.desc'
                }
            }

            if not industry_value:
                random_industry = random.choice(list(industry_dict))
                params.update(industry_dict[random_industry])
                return random_industry

            elif industry_value in industry_dict:
                params.update(industry_dict[industry_value])
                return industry_value

            else:
                speech_text = "I am not sure about {}".format(industry_value)
                reprompt = "Please try again by specifying film industry."
                handler_input.response_builder.speak(speech_text).ask(reprompt)

        slots = handler_input.request_envelope.request.intent.slots

        if indent_slots['date_slot'] in slots and slots[indent_slots['date_slot']].value:
            date_value = slots[indent_slots['date_slot']].value
            handler_input.attributes_manager.session_attributes[indent_slots['date_slot_key']] = date_value

            industry_value = ''
            if indent_slots['industry_slot'] in slots:
                industry_value = slots[indent_slots['industry_slot']].value
                handler_input.attributes_manager.session_attributes[indent_slots['industry_slot_key']] = industry_value

            request_url = "https://api.themoviedb.org/3/discover/movie"
            parameters = {
                'api_key': 'c0f06b953bd8a08dfaef7196d198b463',
                'sort_by': 'release_date.asc',
            }

            # Sets the date range parameter based on user input date
            set_date_parameters(parameters, date_value)
            industry_value = set_industry_parameters(parameters, industry_value)

            response = requests.get(request_url, params=parameters).json()
            movies = []
            card_movies = []

            if response['total_results']:
                speech_text = "The movies releasing in {} are: ".format(industry_value)
                card_text = speech_text + '\n'

                for i, item in enumerate(response['results'][:5]):
                    movies.append(item['title'])
                    card_movies.append(str(i+1) + '. ' + item['title'])

                speech_text += ', '.join(movies).replace('&', 'and')
                card_text += '\n'.join(card_movies)

                if len(response['results']) > 5:
                    speech_text += ", and many more."
                    card_text += ", and many more."

            else:
                speech_text = "There are no movies releasing on {}".format(date_value)

            handler_input.response_builder.speak(speech_text).set_card(
                SimpleCard("Movie Releases", card_text)).set_should_end_session(True)

        else:
            speech_text = "I am not sure what you said.  "
            reprompt = "You can ask by saying, movies releasing this week in Hollywood."

            handler_input.response_builder.speak(speech_text).ask(reprompt)

        return handler_input.response_builder.response


sb.add_request_handler(LaunchRequestHandler())
sb.add_request_handler(HelpIntentHandler())
sb.add_request_handler(CancelOrStopIntentHandler())
sb.add_request_handler(FallbackIntentHandler())
sb.add_request_handler(SessionEndedRequestHandler())

# Custom
sb.add_request_handler(GetUpcomingMoviesHandler())
sb.add_request_handler(GetMovieReleasesHandler())

sb.add_exception_handler(CatchAllExceptionHandler())

handler = sb.lambda_handler()
