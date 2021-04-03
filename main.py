import os
import time
import re
from slackclient import SlackClient
from collections import *
import json
import random
import requests

# load environment variables
from os.path import join, dirname
from dotenv import load_dotenv, find_dotenv
dotenv_path = join(dirname(__file__), '.env')
load_dotenv(dotenv_path, override=True)

slack_client = SlackClient(os.environ.get('SLACK_BOT_TOKEN'))
# starterbot's user ID in Slack: value is assigned after the bot starts up
bot_id = None

# CONSTANTS
RTM_READY_DELAY = 1 # 1 second delay between reading from RTM
EXAMPLE_COMMAND = "help"
MENTION_REGEX = "^<@(|[WU].+?)>(.*)"
ADD_USER_REGEX = "<@(|[WU].+?)>"
CHOICES = {}
SORTS = {}
FAKE_FUNCTIONS = ['umarfc']
FAKE_SORTS = ['umar']
NUMBER_ENDPOINTS = ['trivia', 'year', 'date', 'math']
TEXT_FILE = lambda name: "standup_" + name + ".txt"

# PR Label names
BOX_1 = None # default box
member_list = open("standup.txt", "r") # standup list
BOX_3 = deque(filter(None, member_list.read().split('\n')))
member_list.close()
member_list = open("backup.txt", "r") # backup list
BOX_4 = deque(filter(None, member_list.read().split('\n')))
member_list.close()

def show_table(command, sender, table=BOX_3):
    print
    'in show_table func'
    if len(table) < 1:
        return 'The table is empty!'
    else:
        tableString = 'The table contains:\n'
        for member in table:
            reviewer = slack_client.api_call("users.info", user=member)
            tableString += (reviewer['user']['name'] + '\n')
        return tableString

def show_standup_table(command, sender):
    print
    'in show_standup_table func'
    commands = command.split(' ')
    if (len(commands) < 2):
        return show_table(command, sender, BOX_3)
    else:
        try:
            file = open(TEXT_FILE(commands[1].lower()), 'r')
            return show_table(command, sender, deque(filter(None, file.read().split('\n'))))
        except:
            return "The standup list does not exist"

def show_umarfc(command, sender):
    print
    'in show_umarfc func'
    dm_channel = slack_client.api_call("conversations.open", users=sender)['channel']['id']
    if (sender in BOX_4):
        return {
            'text': show_table(command, sender, BOX_4),
            'channel': dm_channel
        }
    else:
        return {
            'text': "YOUR NOT PART OF THE UAMR FOTBALL CLUB",
            'channel': dm_channel
        }

def drop_table(command, sender, table=BOX_3, name=None):
    print
    'in drop_table func'
    name = name.lower()
    if (name):
        try:
            file = open("standup_"+name+".txt", "r")
            table = deque(filter(None, file.read().split('\n')))
            if len(table) < 1:
                return 'The table is already empty'
            else:
                table.clear()
                save_table_to_file(table, name)
                return 'The table has been cleared'
        except:
            return "The table does not exist"
    else:
        if len(table) < 1:
            return 'The table is already empty'
        else:
            table.clear()
            save_table_to_file(table)
            return 'The table has been cleared'

def drop_standup_table(command, sender):
    commands = command.split(' ')
    print
    'in drop_standup_table func'
    if (len(commands) < 2):
        return drop_table(command, sender, BOX_3)
    else:
        return drop_table(command, sender, BOX_1, commands[1])

def drop_umarfc(command, sender):
    print
    'in drop_umarfc func'
    return drop_table(command, sender, BOX_4)

def list_commands(command, sender):
    print
    'in list_commands func'
    commandList = 'Here are a list of commands:\n'
    for key, value in CHOICES.items():
        if (key not in FAKE_FUNCTIONS):
            commandList += (key + '\n')
    commandList += "For a full explanation of all commands, view the README here:\n"
    commandList += "https://github.com/YangF0917/ACJBot"
    return commandList

def add_to_table(command, sender, group=None, table=BOX_3):
    print
    'in add_to_BOX_1 func'
    message = [n for n in filter(lambda k: k!=group, command.split(' '))] if group else command.split(' ')
    group = group.lower()
    users_added = 0
    if len(message) > 1:
        for token in range(1, len(message)):
            match = re.search(ADD_USER_REGEX, message[token])
            if match:
                if group:
                    file = open(TEXT_FILE(group), "a")
                    mem_list = open(TEXT_FILE(group), "r")
                    BOX = deque(filter(None, mem_list.read().split('\n')))
                    if (match.group(1) not in BOX):
                        BOX.append(match.group(1))
                        save_table_to_file(BOX, group)
                        users_added += 1
                elif match.group(1) not in table:
                    table.append(match.group(1))
                    save_table_to_file(table)
                    users_added += 1
                else:
                    print
                    'User already exists at the table'
            else:
                return 'Users to add must be in the form of "@USER"'

        return '{} users added to the table!'.format(users_added)
    return 'No user to add'

def add_to_standup_table(command, sender):
    print
    'in add_to_standup_table func'
    params = command.split(' ')
    if (len(params) <= 2):
        return add_to_table(command, sender, None, BOX_3)
    elif (re.search(ADD_USER_REGEX, params[1]):
        return add_to_table(command, sender, params[1])

def add_to_umarfanclub(command, sender, table = BOX_4):
    print
    'in add_to_umarfanclub func'
    if sender not in table:
        table.append(sender)
        save_table_to_file(table)
    else:
        print
        'User already exists at the table'

def remove_from_table(command, sender, table=BOX_3):
    print
    'in remove_from_table func'
    message = command.split(' ')
    if len(message) > 1:
        match = re.search(ADD_USER_REGEX, message[1])
        if match:
            if table.count(match.group(1)) < 1:
                return 'No user found to remove'
            else:
                # top_of_list = table[0]
                table.remove(match.group(1))
                save_table_to_file(table)
                return '<@{}> removed from the table!'.format(match.group(1))
    return '"remove @<user>" to remove a member of the table.'

def remove_from_standup_table(command, sender):
    print
    'in remove_from_standup_table func'
    return remove_from_table(command, sender, BOX_3)

def remove_from_umarfc(command, sender, table=BOX_4):
    print
    'in remove_from_umarfc func'
    if sender in table:
        table.remove(sender)
        save_table_to_file(table)
    else:
        print
        'User is not currently in the fanclub'

def sort_help():
    print
    "in sort_help"
    sortList = "Here is the list of sorts:\n"
    for key in SORTS.keys():
        if (key not in FAKE_SORTS):
            sortList += (key + '\n')
    sortList += "You can probably figure out what each one is ;)\nOr you could just read the documentation on https://github.com/YangF0917/ACJBot"
    return sortList

def choose_standup_order(command, sender, table=BOX_3):
    print
    "in choose_standup_order"

    command_string = command.split(' ')
    if len(command_string) == 1 or command_string[1] not in SORTS:
        return sort_help()

    if len(table) < 1:
        return 'The table is empty!'
    else:
        tableString = 'This week\'s standup order:\n'
        temp = SORTS[command_string[1]](command, sender)
        if (len(command_string) > 2 and command_string[2] == "pickme"):
            sender_name = get_name(sender)
            temp.insert(0, temp.pop(temp.index(sender_name))) if sender_name in temp else temp
        elif (len(command_string) > 2 and command_string[2] == "last"):
            sender_name = get_name(sender)
            temp.append(temp.pop(temp.index(sender_name))) if sender_name in temp else temp
        elif (len(command_string) > 2 and command_string[1] != 'umar'):
            match = re.search(MENTION_REGEX, command_string[2])
            volunteer = [get_name(match.group(1))]
            temp.insert(0, temp.pop(temp.index(volunteer[0]))) if len(volunteer) else temp
        
        for member in temp:
            tableString += member
        return {
            'text': tableString,
            'channel': slack_client.api_call("conversations.open", users=sender)['channel']['id'] if command_string[1] == 'umar' else None
        }

def alpha_order(command, sender, table=BOX_3):
    return sorted(map(get_name, table))

def reverse_alpha_order(command, sender, table=BOX_3):
    return sorted(map(get_name, table), reverse=True)

def name_length_order(command, sender, table=BOX_3):
    return sorted(map(get_name, table), key = len)

def rev_name_length_order(command, sender, table=BOX_3):
    return sorted(map(get_name, table), key = len, reverse = True)

def randomize_standup(command, sender, table=BOX_3):
    users = [mem for mem in table]
    random.shuffle(users)
    return map(get_name, users)

def advice(command, sender):
    advice_obj = requests.get('https://api.adviceslip.com/advice')
    # theres 217 unique advice slips
    return str(advice_obj.json()['slip']['advice'])

def number(command, sender):
    random_endpoint = NUMBER_ENDPOINTS[random.randrange(4)]
    number_obj = requests.get('http://numbersapi.com/random/' + random_endpoint + '?json')
    return str(number_obj.json()['text'])

def umar(command, sender, random = False, table = BOX_3):
    slack_client.api_call("conversations.open", users=sender)['channel']['id']
    command_string = command.split(' ')
    num_umars = 10 if (len(command_string) < 3 or not is_valid_number(command_string[2])) else int(command_string[2])
    if (num_umars > 15):
        add_to_umarfanclub(command, sender)
        return ["Welcome to the Umar fanclub :eyes:"]
    elif (num_umars < 1):
        remove_from_umarfc(command, sender)
        return ["You've been removed from the club"]
    return [name for name in filter(lambda name: "umar" in name.lower(), map(get_name, table))] * num_umars

def is_valid_number(string):
    if string[0] == "-":
        string = string[1:]
    for i in string:
        if (ord(i) < ord('0') or ord(i) > ord('9')):
            return False
    return True

def get_name(member):
    temp = slack_client.api_call("users.info", user=member)
    return temp['user']['name'] + '\n'

# === ALL POSSIBLE BOT COMMANDS END ===

# === BOT COMMAND MAPPING ===

CHOICES['sushowtable'] = show_standup_table
CHOICES['sudroptable'] = drop_standup_table
CHOICES['help'] = list_commands
CHOICES['suadd'] = add_to_standup_table
CHOICES['suremove'] = remove_from_standup_table
CHOICES['sort'] = choose_standup_order
CHOICES['umarfc'] = show_umarfc
CHOICES['advice'] = advice
CHOICES['number'] = number

# sorts
SORTS['alpha'] = alpha_order
SORTS['ralpha'] = reverse_alpha_order
SORTS['length'] = name_length_order
SORTS['rlength'] = rev_name_length_order
SORTS['random'] = randomize_standup
SORTS['umar'] = umar

# === BOT COMMAND MAPPING END ===

def command_list(index, command, sender):
    result = CHOICES.get(index, None)
    if result != None:
        result = result(command, sender)
    return result

def save_table_to_file(table=BOX_3, name=None):
    if (name):
        member_list = open(TEXT_FILE(name), "w")
    elif(table == BOX_3):
        member_list = open("standup.txt", "w")
    elif(table == BOX_4):
        member_list = open("backup.txt", "w")
    else:
        print("something went wrong!")
    file_buffer = ''
    for member in table:
        file_buffer += member + '\n'
    member_list.write(file_buffer)
    member_list.close()

def parse_bot_commands(slack_events):
    """
        Parses a list of events coming from the Slack RTM API to find bot commands.
        If a bot command is found, this function returns a tuple of command and channel.
        If its not found, then this function returns None, None.
    """
    for event in slack_events:
        if event["type"] == "message" and not "subtype" in event:
            user_id, message = parse_direct_mention(event["text"])
            if user_id == codereviewbot_id:
                return message, event["channel"], event["user"]
    return None, None, None

def parse_direct_mention(message_text):
    """
        Finds a direct mention (a mention that is at the beginning) in message text
        and returns the user ID which was mentioned. If there is no direct mention, returns None
    """
    matches = re.search(MENTION_REGEX, message_text)
    # the first group contains the username, the second group contains the remaining message
    return (matches.group(1), matches.group(2).strip()) if matches else (None, None)

def handle_command(command, channel, sender):
    """
        Executes bot command if the command is known
    """
    # Default response is help text for the user
    default_response = "Not sure what you mean. Type *{}* for a list of commands.".format(EXAMPLE_COMMAND)

    # Finds and executes the given command, filling in response
    response = None

    # This is where you start to implement more commands!
    command_switch = command.split(' ')[0]

    response = command_list(command_switch, command, sender)
    # Sends the response back to the channel
    if isinstance(response, str) or isinstance(response, basestring) or response is None:
        slack_client.api_call(
            "chat.postMessage",
            channel=channel,
            text=response or default_response
        )
    elif (response['text']):
        slack_client.api_call(
            "chat.postMessage",
            channel=response['channel'] if response['channel'] else channel,
            text=response['text']
        )
    else:
        slack_client.api_call(
            "chat.postMessage",
            channel=channel,
            text=response['text'] or default_response,
            attachments=response['attachment']
        )

if __name__ == "__main__":
    if slack_client.rtm_connect(with_team_state=False, auto_reconnect=True):
        print("ACJ Bot connected and running!")
        # Read bot's user ID by calling web API method `auth.test`
        codereviewbot_id = slack_client.api_call("auth.test")["user_id"]
        while True:
            command, channel, sender = parse_bot_commands(slack_client.rtm_read())
            if command:
                handle_command(command, channel, sender)
            time.sleep(RTM_READY_DELAY)
    else:
        print("Connection failed.")
