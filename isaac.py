# figured out these codes from looking online at tutorials
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

# global variables

direction_slot = "direction"
block_type_slot = "block_type"
pos_str = "position"
grid_str = "grid"
zombies_str = "zombies"
cols = 20
rows = 20
start_time_str = "start_time"
build_time_limit = 60 # seconds

# this makes it so all the words are using the same voice
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
        x, y = handler_input.attributes_manager.session_attributes[pos_str]
        handler_input.attributes_manager.session_attributes[grid_str] = [[0]*cols]*rows
        speak_output = wrap_speak("""
		<audio src="soundbank://soundlibrary/explosions/explosions/explosions_03"/>
		AAAAH! Monsters are coming lets build defenses! You are on a {} by {} grid at position {}, {}. What's your first order?""".format(cols, rows, x, y))

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

def reset_timer(input):
    input.attributes_manager.session_attributes[start_time_str] = time.time()

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

# Make 5 normal zombies
def create_normal_zombies():
    z1 = (3,rows)
    z2 = (8,rows)
    z3 = (5,rows)
    z4 = (10,rows)
    z5 = (12,rows)

    return [z1, z2, z3, z4, z5]

def zombie_event(handler_input):
    speak_output = "oh no! they're coming!"

    zombies = create_normal_zombies()
    is_game_over, script = move_zombies(handler_input, zombies)
    speak_output += script
    speak_output = wrap_speak(speak_output)
    result = handler_input.response_builder.speak(speak_output)

    # Check to see if it is game over
    if not is_game_over:
        reset_timer(handler_input)
        result = result.ask(speak_output)
    else:
        result = result.set_should_end_session(True)

    return result.response

def move_zombies(input, zombies):

    # Get a list of all zombies
    #zombies = input.attributes_manager.session_attributes[zombies_str]

    # Get the grid to find out where blocks are
    grid = input.attributes_manager.session_attributes[grid_str]

    # where we are standing
    pos = input.attributes_manager.session_attributes[pos_str]

    # variable that make event talk stuff from Alexa
    script = ""

    is_game_over = False

    # Loop while zombies are still on the grid
    while len(zombies) > 0 and not is_game_over:

        updated_zombie_locations = []
        
        # Loop through every zombie and move it forward one if there are no blocks. If there is a block
        # then destroy one of the blocks.
        for zx, zy in zombies:
            print("You are at %d, %d, zombie at %d %d" % (pos[0], pos[1], zx, zy))
            if (zy-1) < 0:
                # zombie moved off of grid or screen
                continue
            elif grid[zx][zy-1] > 0:
                # Zombie destroys a block, but doesn't move forward
                grid[zx][zy-1] -= 1
                updated_zombie_locations.append((zx, zy))

                # say zombie breaks block
                script += """<audio src="soundbank://soundlibrary/wood/breaks/breaks_06"/> A zombie tore through a block! """
            elif zx == pos[0] and (zy-1) == pos[1]:
                script += """<audio src="soundbank://soundlibrary/human/amzn_sfx_baby_big_cry_01"/> uh oh you perished! game over! """
                is_game_over = True
                break
            elif grid[zx][zy-1] == 0:
                # Move zombie forward, but don't say anything
                zombie_pos = (zx, zy-1)
                updated_zombie_locations.append(zombie_pos)

        zombies = updated_zombie_locations

    if not is_game_over:
        script += """phew, they are gone"""

    input.attributes_manager.session_attributes[grid_str] = grid
    print(script)
    return is_game_over, script

# Make sure that the blocks people ask for we can build
block_sizes = ["2 by 2", "1 by 1", "3 by 3", "corner", "1 by 2"]
def is_correct_block(block_type):
    logger.error(block_type)
    if block_type in block_sizes:
        return True
    else:
        return False

# this is where we build blocks by adding them to the grid
def add_block_to_grid(block_type, x, y, grid):
    if block_type == "2 by 2":
        grid[x][y] += 1
        grid[x+1][y] += 1
        grid[x][y+1] += 1
        grid[x+1][y+1] += 1
    elif block_type == "1 by 1":
        grid[x][y] += 1
    elif block_type == "corner":
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

# This is used to help debug the program--it is something that a typical player won't see
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
            return zombie_event(handler_input)

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
        start_timer(handler_input)

        speak_output = ""

        if is_time_up(handler_input):
            return zombie_event(handler_input)

        x, y = handler_input.attributes_manager.session_attributes[pos_str]
        slots = handler_input.request_envelope.request.intent.slots
        if direction_slot in slots:
            direction = slots[direction_slot].value
            x, y = handler_input.attributes_manager.session_attributes[pos_str]
            if (direction == "up" or direction == "north" or direction == "forward"):
                y += 1
            elif (direction == "down" or direction == "south" or direction == "back" or direction == "backward"):
                y -= 1
            elif (direction == "left" or direction == "west"):
                x -= 1
            elif (direction == "right" or direction == "east"):
                x += 1
            else:
                speak_output += "I don't know how to move in that direction. "

            handler_input.attributes_manager.session_attributes[pos_str] = (x, y)
            speak_output += "You are now at position {}, {}. What next?".format(x, y)
            speak_output = wrap_speak(speak_output)

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

class FallbackIntentHandler(AbstractRequestHandler):
    """Handler for fallback Intent."""
    def can_handle(self, handler_input):
        # type: (HandlerInput) -> bool
        return ask_utils.is_intent_name("AMAZON.FallbackIntent")(handler_input)

    def handle(self, handler_input):
        # type: (HandlerInput) -> Response
        speak_output = wrap_speak("I'm having trouble understanding. Try moving or building a block.")

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

# the below code was taken from a freely-available tutorial online

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
sb.add_request_handler(FallbackIntentHandler())
sb.add_request_handler(IntentReflectorHandler()) # make sure IntentReflectorHandler is last so it doesn't override your custom intent handlers
sb.add_exception_handler(CatchAllExceptionHandler())

app = Flask(__name__)
app.config['ASK_SDK_VERIFY_TIMESTAMP'] = False
skill_response = SkillAdapter(
    skill=sb.create(), skill_id='amzn1.ask.skill.df7f27ea-302a-487c-852b-725e8e35460d', app=app)

skill_response.register(app=app, route="/")

if __name__ == '__main__':
    app.run()
