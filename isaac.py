from flask import Flask
import logging
import sys
import ask_sdk_core.utils as ask_utils
import time
from ask_sdk_core.skill_builder import SkillBuilder
from flask_ask_sdk.skill_adapter import SkillAdapter
from ask_sdk_core.dispatch_components import AbstractRequestHandler
from ask_sdk_core.dispatch_components import AbstractExceptionHandler
from ask_sdk_core.handler_input import HandlerInput

from ask_sdk_model import Response

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

# globals

direction_slot = "direction"
block_type_slot = "block_type"
pos_str = "position"
grid_str = "grid"
cols = 20
rows = 20
start_time_str = "start_time"
build_time_limit = 60 # seconds

def wrap_speak(speak_str):
	return """<speak><voice name="Matthew">""" + speak_str + """</voice></speak>"""

class LaunchRequestHandler(AbstractRequestHandler):
    """Handler for Skill Launch."""
    def can_handle(self, handler_input):
        # type: (HandlerInput) -> bool

        return ask_utils.is_request_type("LaunchRequest")(handler_input)

    def handle(self, handler_input):
        # type: (HandlerInput) -> Response
        handler_input.attributes_manager.session_attributes[pos_str] = (int(cols/2), int(rows/2))
        handler_input.attributes_manager.session_attributes[grid_str] = [[0]*cols]*rows
        speak_output = wrap_speak("""
		<audio src="soundbank://soundlibrary/explosions/explosions/explosions_03"/>
		AAAAH! Monsters are coming lets build defenses! You are on a {} by {} grid. What's your first order?""".format(cols, rows))

        return (
            handler_input.response_builder
                .speak(speak_output)
                .ask(speak_output)
                .response
        )

def get_time(input):
    if start_time_str in input.attributes_manager.session_attributes:
        return int(input.attributes_manager.session_attributes[start_time_str])
    else:
        return 0

def start_timer(input):
    if get_time(input) == 0:
        input.attributes_manager.session_attributes[start_time_str] = time.time()

def is_time_up(input):
    start_time = get_time(input)
    if start_time <= 0:
        return False

    if (time.time() - start_time) >= build_time_limit:
        return True
    else:
        return False

block_sizes = ["2 by 2", "1 by 1", "3 by 3", "l", "1 by 2"]

def is_correct_block(block_type):
    logger.error(block_type)
    if block_type in block_sizes:
        return True
    else:
        return False

def add_block_to_grid(block_type, x, y, grid):
    if block_type == "2 by 2":
        grid[x][y] += 1
        grid[x+1][y] += 1
        grid[x][y+1] += 1
        grid[x+1][y+1] += 1
    elif block_type == "1 by 1":
        grid[x][y] += 1
    elif block_type == "l":
        grid[x][y] += 1
        grid[x][y+1] += 1
        grid[x+1][y+1] += 1
    elif block_type == "3 by 3":
        grid[x][y] += 1
        grid[x+1][y] += 1
        grid[x+2][y] += 1
        grid[x][y+1] += 1
        grid[x+2][y+1] += 1
        grid[x+1][y+1] += 1
        grid[x][y+2] += 1
        grid[x+1][y+2] += 1
        grid[x+2][y+2] += 1
    elif block_type == "1 by 2":
        grid[x][y] += 1
        grid[x+1][y] += 1

def print_grid(grid):
    y = rows - 1
    x = 0
    while (y >= 0):
        while (x < cols):
            sys.stdout.write(str(grid[x][y]) + " ")
            x += 1
        sys.stdout.write("\n")
        x = 0
        y -= 1

class BuildIntentHandler(AbstractRequestHandler):
    """Handler for building."""
    def can_handle(self, handler_input):
        # type: (HandlerInput) -> bool
        return ask_utils.is_intent_name("Build")(handler_input)

    def handle(self, handler_input):
        # type: (HandlerInput) -> Response
        start_timer(handler_input)

        if is_time_up(handler_input):
            speak_output = wrap_speak("oh no! they're coming!")
            return(
                handler_input.response_builder
                .speak(speak_output)
                .ask(speak_output)
                .response
            )

        slots = handler_input.request_envelope.request.intent.slots
        
        if block_type_slot in slots:
            block_type = slots[block_type_slot].value

            # Check for correct block types
            if is_correct_block(block_type):
                # Add logic to build something on the grid
                x, y = handler_input.attributes_manager.session_attributes[pos_str]
                grid = handler_input.attributes_manager.session_attributes[grid_str]
                add_block_to_grid(block_type, x, y, grid)
                handler_input.attributes_manager.session_attributes[grid_str] = grid
                print_grid(grid)
                speak_output = wrap_speak("You are building a {} block.".format(block_type))
            else:
                speak_output = wrap_speak("Hmmmmm. I can't build a {} block.".format(block_type))

        return (
            handler_input.response_builder
                .speak(speak_output)
                .ask(speak_output)
                .response
        )


class MoveIntentHandler(AbstractRequestHandler):
    """Handler for Moving."""
    def can_handle(self, handler_input):
        # type: (HandlerInput) -> bool
        return ask_utils.is_intent_name("Move")(handler_input)

    def handle(self, handler_input):
        # type: (HandlerInput) -> Response
        slots = handler_input.request_envelope.request.intent.slots
        x, y = handler_input.attributes_manager.session_attributes[pos_str]

        if direction_slot in slots:
            direction = slots[direction_slot].value
            x, y = handler_input.attributes_manager.session_attributes[pos_str]
            if (direction == "up" or direction == "north"):
                y += 1
            elif (direction == "down" or direction == "south"):
                y -= 1
            elif (direction == "left" or direction == "west"):
                x -= 1
            else:
                x += 1

            handler_input.attributes_manager.session_attributes[pos_str] = (x, y)
            speak_output = wrap_speak("You are now at position {} , {}. What next?".format(x, y))

        return (
            handler_input.response_builder
                .speak(speak_output)
                .ask(speak_output)
                .response
        )

class HelpIntentHandler(AbstractRequestHandler):
    """Handler for Help Intent."""
    def can_handle(self, handler_input):
        # type: (HandlerInput) -> bool
        return ask_utils.is_intent_name("AMAZON.HelpIntent")(handler_input)

    def handle(self, handler_input):
        # type: (HandlerInput) -> Response
        speak_output = "You can say hello to me! How can I help?"

        return (
            handler_input.response_builder
                .speak(speak_output)
                .ask(speak_output)
                .response
        )


class CancelOrStopIntentHandler(AbstractRequestHandler):
    """Single handler for Cancel and Stop Intent."""
    def can_handle(self, handler_input):
        # type: (HandlerInput) -> bool
        return (ask_utils.is_intent_name("AMAZON.CancelIntent")(handler_input) or
                ask_utils.is_intent_name("AMAZON.StopIntent")(handler_input))

    def handle(self, handler_input):
        # type: (HandlerInput) -> Response
        speak_output = "Goodbye!"

        return (
            handler_input.response_builder
                .speak(speak_output)
                .response
        )


class SessionEndedRequestHandler(AbstractRequestHandler):
    """Handler for Session End."""
    def can_handle(self, handler_input):
        # type: (HandlerInput) -> bool
        return ask_utils.is_request_type("SessionEndedRequest")(handler_input)

    def handle(self, handler_input):
        # type: (HandlerInput) -> Response

        # Any cleanup logic goes here.

        return handler_input.response_builder.response


class IntentReflectorHandler(AbstractRequestHandler):
    """The intent reflector is used for interaction model testing and debugging.
    It will simply repeat the intent the user said. You can create custom handlers
    for your intents by defining them above, then also adding them to the request
    handler chain below.
    """
    def can_handle(self, handler_input):
        # type: (HandlerInput) -> bool
        return ask_utils.is_request_type("IntentRequest")(handler_input)

    def handle(self, handler_input):
        # type: (HandlerInput) -> Response
        intent_name = ask_utils.get_intent_name(handler_input)
        speak_output = "You just triggered " + intent_name + "."

        return (
            handler_input.response_builder
                .speak(speak_output)
                # .ask("add a reprompt if you want to keep the session open for the user to respond")
                .response
        )


class CatchAllExceptionHandler(AbstractExceptionHandler):
    """Generic error handling to capture any syntax or routing errors. If you receive an error
    stating the request handler chain is not found, you have not implemented a handler for
    the intent being invoked or included it in the skill builder below.
    """
    def can_handle(self, handler_input, exception):
        # type: (HandlerInput, Exception) -> bool
        return True

    def handle(self, handler_input, exception):
        # type: (HandlerInput, Exception) -> Response
        logger.error(exception, exc_info=True)

        speak_output = "Sorry, I had trouble doing what you asked. Please try again."

        return (
            handler_input.response_builder
                .speak(speak_output)
                .ask(speak_output)
                .response
        )

# The SkillBuilder object acts as the entry point for your skill, routing all request and response
# payloads to the handlers above. Make sure any new handlers or interceptors you've
# defined are included below. The order matters - they're processed top to bottom.

sb = SkillBuilder()

# Register all handlers, interceptors etc.
sb.add_request_handler(LaunchRequestHandler())
sb.add_request_handler(MoveIntentHandler())
sb.add_request_handler(BuildIntentHandler())
#sb.add_request_handler(HelloWorldIntentHandler())
sb.add_request_handler(HelpIntentHandler())
sb.add_request_handler(CancelOrStopIntentHandler())
sb.add_request_handler(SessionEndedRequestHandler())
sb.add_request_handler(IntentReflectorHandler()) # make sure IntentReflectorHandler is last so it doesn't override your custom intent handlers
sb.add_exception_handler(CatchAllExceptionHandler())

app = Flask(__name__)
app.config['ASK_SDK_VERIFY_TIMESTAMP'] = False
skill_response = SkillAdapter(
    skill=sb.create(), skill_id='amzn1.ask.skill.df7f27ea-302a-487c-852b-725e8e35460d', app=app)

skill_response.register(app=app, route="/")

if __name__ == '__main__':
    app.run()
