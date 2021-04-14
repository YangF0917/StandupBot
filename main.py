# coding: utf8
import os
import time
import re
from slackclient import SlackClient
from collections import *
import json
import random
import requests
import schedule
import copy
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
EXAMPLE_COMMAND = 'help'
MENTION_REGEX = '^<@(|[WU].+?)>(.*)'
ADD_USER_REGEX = '<@(|[WU].+?)>'
USER_ID = '[WU]\w{10}?'
TIME_REGEX = '^([01]?[0-9]|2[0-3]):[0-5][0-9]$'
TEAM_NAME_REGEX = '^\w+$'
CHOICES = {}
SORTS = {}
BACKUP_OPTIONS = ['add', 'restore', 'remove', 'show']
FAKE_FUNCTIONS = ['umarfc']
FAKE_SORTS = ['umar']
NUMBER_ENDPOINTS = ['trivia', 'year', 'date', 'math']
CHANNEL_REQ = ['ps', 'sort', 'umarfc', 'remove', 'removeteam']
EMPTY_TEAM = {
        'postscrum': {
            'channel': '',
            'message': 'Postscrum? :eyes:',
            'time': '',
            'timestamp': '',
        },
        'members' : {}
    }
EMPTY_MEMBER = {
        'has_postscrum': False,
    }

# default messages
TEAM_DOES_NOT_EXIST = 'That team doesn\'t exist.'
NO_NAME = 'Please specify a team name.'
INVALID_NAME = 'Please provide a valid team name.'
CHANNEL_ONLY = 'This command can only be used in a channel.'
EMPTY_TEAM = 'That team is empty :pensive:'

# initialize objects
with open('ufc.json') as f:
  UMAR_FC = json.load(f)
with open('standup.json') as f:
  STANDUP_TEAMS = json.load(f)
with open('backup.json') as f:
  BACKUP = json.load(f)

# === BOT COMMANDS ===

def show_team(command, sender):
    params = command.split(' ')
    if len(params) < 2:
        return NO_NAME
    name = params[1].lower()
    if name not in STANDUP_TEAMS:
        return TEAM_DOES_NOT_EXIST
    team = STANDUP_TEAMS[name]
    if len(team['members']) == 0:
        return EMPTY_TEAM
    else:
        update_reactions(name)
        output = f'{name} consists of the following members:\n'
        for member in team['members']:
            output += f'\t{get_name(member)}' + (' :hand:' if team['members'][member]['has_postscrum'] else '') + '\n'
        return output

def show_teams(command, sender):
    if not len(STANDUP_TEAMS):
        return 'There are no teams here.'
    output = 'Stored teams are as follows: \n'
    for key in STANDUP_TEAMS:
        output += f'\t{key}\n'
    return output
    
def remove_team(command, sender, channel):
    if (channel[0] != 'C'):
        return CHANNEL_ONLY
    params = command.split(' ')
    if len(params) < 2:
        return NO_NAME
    name = params[1].lower()
    if name not in STANDUP_TEAMS:
        return TEAM_DOES_NOT_EXIST
    STANDUP_TEAMS.pop(name)
    save_json(STANDUP_TEAMS)
    return f'<@{sender}> has removed {name} from the list of teams.'

def add_team(command, sender):
    params = command.split(' ')
    if len(params) < 2:
        return NO_NAME
    name = params[1].lower()
    if (not is_valid_team_name(name)):
        return INVALID_NAME
    if name in STANDUP_TEAMS:
        return 'A team with this name already exists.'
    STANDUP_TEAMS[name] = copy.deepcopy(EMPTY_TEAM)
    save_json(STANDUP_TEAMS)
    return f'{name} has been added to the teams list.'

def backup_usage():
    output = 'Use `backup` with one of the following options:\n'
    output += '\t`show`: Shows all teams currently stored in the backup file.\n'
    output += '\t`add <team>`: Backs up the specified team.\n'
    output += '\t`restore <team>`: Restores the specified team to the standup list.\n'
    output += '\t`remove <team>`: Removes the specified team from the backup file.'
    return output

def handle_backup(command, sender): # TODO maybe: add a time for when the backup was created?
    params = command.split(' ')
    if len(params) > 1 and params[1].lower() == 'show':
        if not len(BACKUP):
            return 'There are no teams backed up.'
        output = 'Backed up teams are as follows: \n'
        for key in BACKUP:
            output += f'\t{key}\n'
        return output
    elif len(params) > 2 and params[1].lower() in BACKUP_OPTIONS:
        option = params[1].lower()
        team = params[2].lower()
        if (not is_valid_team_name(team)):
            return INVALID_NAME
        if option == 'add':
            if team not in STANDUP_TEAMS:
                return TEAM_DOES_NOT_EXIST
            BACKUP[team] = copy.deepcopy(STANDUP_TEAMS[team])
            save_json(BACKUP, 'backup.json')
            return f'{team} has been backed up to the file.'
        elif option == 'restore':
            if team not in BACKUP:
                return 'That team hasn\'t been backed up.'
            STANDUP_TEAMS[team] = copy.deepcopy(BACKUP[team])
            save_json(STANDUP_TEAMS)
            return f'{team} has been restored from the file.'
        else:
            if team not in BACKUP:
                return 'That team hasn\'t been backed up.'
            BACKUP.pop(team)
            save_json(BACKUP, 'backup.json')
            return f'The backup for {team} has been removed from the file.'
    return backup_usage()
    
def save_json(table, file='standup.json'):
    with open(file, 'w') as json_file:
        json.dump(table, json_file, indent = 4, sort_keys=True)

def add_member(command, sender):
    params = command.split(' ')
    if len(params) < 3:
        return 'Try `add <team> @<user>` to add a user to the team.'
    team = params[1].lower()
    if team not in STANDUP_TEAMS:
        return TEAM_DOES_NOT_EXIST
    users_added = 0
    for token in range(2, len(params)):
        match = re.search(ADD_USER_REGEX, params[token])
        if match:
            if match[1] not in STANDUP_TEAMS[team]['members']:
                STANDUP_TEAMS[team]['members'][match[1]] = copy.deepcopy(EMPTY_MEMBER)
                users_added += 1
    if users_added == 0:
        return 'No users added - either they don\'t exist or they\'re already in the team.'
    save_json(STANDUP_TEAMS)
    if users_added == 1:
        return f'A new member just dropped into {team} - say hi! :wave:'
    return f'{users_added} new members just dropped into {team} - say hi! :wave:'    

def remove_member(command, sender, channel):
    if channel[0] != 'C':
        return CHANNEL_ONLY
    params = command.split(' ')
    if len (params) < 3:
        return 'Try `remove <team> @<user>` to remove a user from the team.'
    team = params[1].lower()
    if team not in STANDUP_TEAMS:
        return TEAM_DOES_NOT_EXIST
    users_removed = 0
    for token in range(2, len(params)):
        match = re.search(ADD_USER_REGEX, params[token])
        user_id = params[token][2:-1]
        if match:
            if user_id in STANDUP_TEAMS[team]['members']:
                STANDUP_TEAMS[team]['members'].pop(user_id)
                users_removed += 1
    if users_removed == 0:
        return 'No users were removed - either they don\'t exist, or they weren\'t in this team.'
    save_json(STANDUP_TEAMS)
    if users_removed == 1:
        return f'<@{sender}> just removed someone from the team - say bye! :wave:'
    return f'<@{sender}> just removed {users_removed} members from the team - say bye! :wave:'       

def show_umarfc(command, sender, channel):
    if channel[0] != 'D':
        return list_commands()
    dm_channel = slack_client.api_call('conversations.open', users=sender)['channel']['id']
    if (sender in UMAR_FC['members']):
        if len(UMAR_FC['members']) == 0:
            return 'The club currently has no members :pensive:'
        output = 'The club contains:\n'
        for member in UMAR_FC['members']:
            output += f'\t{get_name(member)}\n'
        return {
            'text': output,
            'channel': dm_channel
        }
    else:
        return {
            'text': 'YOUR NOT PART OF THE UAMR FOTBALL CLUB',
            'channel': dm_channel
        }

def list_commands(command, sender):
    command_list = 'Here is a list of the commands:\n'
    for key, value in CHOICES.items():
        if (key not in FAKE_FUNCTIONS):
            command_list += f'\t{key}\n'
    command_list += 'For a full explanation of all commands, view the README here:\n'
    command_list += 'https://github.com/YangF0917/ACJBot'
    return command_list

def sort_help():
    sort_list = 'Try `sort <team> <sort type>` \nHere is the list of sorts:\n'
    for key in SORTS.keys():
        if (key not in FAKE_SORTS):
            sort_list += f'\t{key}\n'
    sort_list += 'You can probably figure out what each one is ;)\nOr you could just read the documentation on https://github.com/YangF0917/ACJBot'
    return sort_list

def choose_standup_order(command, sender, channel):
    command_string = command.split(' ')
    if len(command_string) < 3 or command_string[2] not in SORTS:
        return sort_help()
    team = command_string[1].lower()
    sort = command_string[2]
    if (sort == 'umar' and channel[0] != 'D'):
        return sort_help()
    if team not in STANDUP_TEAMS:
        return TEAM_DOES_NOT_EXIST
    update_reactions(team)
    team = STANDUP_TEAMS[team]['members']
    if len(team) < 1:
        return EMPTY_TEAM
    else:
        tableString = 'Today\'s standup order:\n'
        temp = SORTS[sort](command, sender, team)
        if (len(command_string) > 3 and command_string[3] == 'pickme'):
            temp.insert(0, temp.pop(temp.index(sender))) if sender in temp else temp
        elif (len(command_string) > 3 and command_string[3] == 'last'):
            temp.append(temp.pop(temp.index(sender))) if sender in temp else temp
        elif (len(command_string) > 3 and command_string[2] != 'umar'):
            match = re.search(MENTION_REGEX, command_string[3])
            volunteer = [match.group(1)]
            temp.insert(0, temp.pop(temp.index(volunteer[0]))) if len(volunteer) else temp
        for member in temp:
            match = re.search(USER_ID, member)
            if match:
                match = match.group(0)
                tableString += f'\t{get_name(match)}' + (' :hand:' if team[match]['has_postscrum'] else '') + '\n'
            else:
                tableString += member
        return {
            'text': tableString,
            'channel': slack_client.api_call('conversations.open', users=sender)['channel']['id'] if command_string[2] == 'umar' else None
        }

def alpha_order(command, sender, table):
    return sorted(table, key = get_name)

def reverse_alpha_order(command, sender, table):
    return sorted(table, key = get_name, reverse=True)

def name_length_order(command, sender, table):
    return sorted(table, key = lambda x: len(get_name(x)))

def rev_name_length_order(command, sender, table):
    return sorted(table, key = lambda x: len(get_name(x)), reverse = True)

def randomize_standup(command, sender, table):
    users = [mem for mem in table]
    random.shuffle(users)
    return users

def advice(command, sender):
    advice_obj = requests.get('https://api.adviceslip.com/advice')
    # theres 217 unique advice slips
    return str(advice_obj.json()['slip']['advice'])

def number(command, sender):
    random_endpoint = NUMBER_ENDPOINTS[random.randrange(4)]
    number_obj = requests.get('http://numbersapi.com/random/' + random_endpoint + '?json')
    return number_obj.json()['text']

def umar(command, sender, table):
    command_string = command.split(' ')
    num_umars = 10 if (len(command_string) < 4 or not is_valid_number(command_string[3])) else int(command_string[3])
    if (num_umars > 15):
        add_to_umarfanclub(sender)
        return ['Welcome to the club :football:']
    elif (num_umars < 1):
        remove_from_umarfanclub(sender)
        return ['You\'ve been removed from the club']
    return [name for name in filter(lambda name: 'umar' in get_name(name).lower(), table)] * num_umars

def add_to_umarfanclub(sender):
    if sender not in UMAR_FC['members']:
        UMAR_FC['members'].append(sender)
    save_json(UMAR_FC, 'ufc.json')
    
def remove_from_umarfanclub(sender):
    if sender in UMAR_FC['members']:
        UMAR_FC['members'].pop(UMAR_FC['members'].index(sender))
    save_json(UMAR_FC,'ufc.json')

def is_valid_number(string):
    if string[0] == '-':
        string = string[1:]
    for i in string:
        if (ord(i) < ord('0') or ord(i) > ord('9')):
            return False
    return True

def is_valid_team_name(string):
    return re.search(TEAM_NAME_REGEX, string)

def get_name(member):
    return slack_client.api_call('users.info', user=member)['user']['name']

def ps_usage():
    output = 'To configure postscrum for your team, use `ps <team>` along with one of the following:\n'
    output += '\t`time [24hr-time]`: Sets the time for the postscrum message to appear in this channel.\n'
    output += '\t`message [message]`: Sets the postscrum message. By default, the message is \'Postscrum? :eyes:\'.\n'
    output += '\t`stop`: Stops postscrum messages from appearing in this channel.\n'
    output += 'Note: Each team can receive postscrum messages in only one channel, and the messages will not appear if a time is not set.'
    return output

def configure_postscrum (command, sender, channel):
    params = command.split(' ')
    if len(params) > 2:
        team = params[1].lower()
        if team not in STANDUP_TEAMS:
            return TEAM_DOES_NOT_EXIST
        if params[2] == 'time' and len(params) > 3:
            match = re.search(TIME_REGEX, params[3])
            if match:
                STANDUP_TEAMS[team]['postscrum']['channel'] = channel
                STANDUP_TEAMS[team]['postscrum']['time'] = ('0' if len(params[3]) == 4 else '') + params[3]
                save_json(STANDUP_TEAMS)
                configure_scheduler()
                return 'Postscrum messages will appear in this channel at ' + STANDUP_TEAMS[team]['postscrum']['time'] + ' every weekday.'
            return 'Please enter a valid time.'
        elif params[2] == 'message' and len(params) > 3:
            STANDUP_TEAMS[team]['postscrum']['channel'] = channel
            STANDUP_TEAMS[team]['postscrum']['message'] = ' '.join(params[3:])
            save_json(STANDUP_TEAMS)
            configure_scheduler()
            return f'Postscrum message has been set to "' + STANDUP_TEAMS[team]['postscrum']['message'] + '".'
        elif params[2] == 'stop':
            if STANDUP_TEAMS[team]['postscrum']['channel'] == '':
                return 'Postscrum messages are not currently set in this channel.'
            STANDUP_TEAMS[team]['postscrum']['channel'] = ''
            STANDUP_TEAMS[team]['postscrum']['time'] = ''
            save_json(STANDUP_TEAMS)
            configure_scheduler()
            return 'Postscrum messages have been stopped in this channel. To reconfigure, use the `time` postscrum option.'
    return ps_usage()


# === ALL POSSIBLE BOT COMMANDS END ===

# === BOT COMMAND MAPPING ===

CHOICES['showteams'] = show_teams
CHOICES['addteam'] = add_team
CHOICES['removeteam'] = remove_team
CHOICES['show'] = show_team
CHOICES['add'] = add_member
CHOICES['remove'] = remove_member
CHOICES['ps'] = configure_postscrum
CHOICES['sort'] = choose_standup_order
CHOICES['umarfc'] = show_umarfc
CHOICES['advice'] = advice
CHOICES['number'] = number
CHOICES['help'] = list_commands
CHOICES['backup'] = handle_backup

# sorts
SORTS['alpha'] = alpha_order
SORTS['ralpha'] = reverse_alpha_order
SORTS['length'] = name_length_order
SORTS['rlength'] = rev_name_length_order
SORTS['random'] = randomize_standup
SORTS['umar'] = umar

# === BOT COMMAND MAPPING END ===

def update_reactions(team):
    if STANDUP_TEAMS[team]['postscrum']['timestamp']:
        reset_reactions(team)
        message_obj = slack_client.api_call(
            'reactions.get',
            channel=STANDUP_TEAMS[team]['postscrum']['channel'],
            timestamp=STANDUP_TEAMS[team]['postscrum']['timestamp'],
            full=False,
        )['message']
        if 'reactions' in message_obj:
            users_reacted = []
            for reaction in message_obj['reactions']:
                users_reacted += reaction['users']
            users_reacted = list(set(users_reacted))
            users_reacted = list(filter(lambda user: user in STANDUP_TEAMS[team]['members'], users_reacted))
            for user in users_reacted:
                STANDUP_TEAMS[team]['members'][user]['has_postscrum'] = True
            save_json(STANDUP_TEAMS)

def reset_reactions(team):
    for user in STANDUP_TEAMS[team]['members']:
        STANDUP_TEAMS[team]['members'][user]['has_postscrum'] = False
    save_json(STANDUP_TEAMS)

def daily_postscrum(team):
    reset_reactions(team)
    STANDUP_TEAMS[team]['postscrum']['timestamp'] = slack_client.api_call(
        'chat.postMessage',
        channel=STANDUP_TEAMS[team]['postscrum']['channel'],
        text=STANDUP_TEAMS[team]['postscrum']['message']
    )['message']['ts']
    save_json(STANDUP_TEAMS)

def configure_scheduler():
    teams = list(filter(lambda team: STANDUP_TEAMS[team]['postscrum']['channel'] != '' and STANDUP_TEAMS[team]['postscrum']['time'] != '', STANDUP_TEAMS.keys()))
    schedule.clear()
    for team in teams:
        time = STANDUP_TEAMS[team]['postscrum']['time']
        schedule.every().monday.at(time).do(daily_postscrum, team)
        schedule.every().tuesday.at(time).do(daily_postscrum, team)
        schedule.every().wednesday.at(time).do(daily_postscrum, team)
        schedule.every().thursday.at(time).do(daily_postscrum, team)
        schedule.every().friday.at(time).do(daily_postscrum, team)

def command_list(index, command, sender, channel):
    result = CHOICES.get(index, None)
    if result == None:
        return None

    if index in CHANNEL_REQ:
        result = result(command, sender, channel)
    else:
        result = result(command, sender)
    return result


def parse_bot_commands(slack_events):
    '''
        Parses a list of events coming from the Slack RTM API to find bot commands.
        If a bot command is found, this function returns a tuple of command and channel.
        If its not found, then this function returns None, None.
    '''
    for event in slack_events:
        if event['type'] == 'message' and not 'subtype' in event:
            user_id, message = parse_direct_mention(event['text'])
            if user_id == codereviewbot_id:
                return message, event['channel'], event['user']
    return None, None, None

def parse_direct_mention(message_text):
    '''
        Finds a direct mention (a mention that is at the beginning) in message text
        and returns the user ID which was mentioned. If there is no direct mention, returns None
    '''
    matches = re.search(MENTION_REGEX, message_text)
    # the first group contains the username, the second group contains the remaining message
    return (matches.group(1), matches.group(2).strip()) if matches else (None, None)

def handle_command(command, channel, sender):
    '''
        Executes bot command if the command is known
    '''
    # Default response is help text for the user
    default_response = f'Not sure what you mean. Try `{EXAMPLE_COMMAND}` for a list of commands.'

    # Finds and executes the given command, filling in response
    response = None

    # This is where you start to implement more commands!
    command_switch = command.split(' ')[0]

    response = command_list(command_switch, command, sender, channel)
    
    # Sends the response back to the channel
    if isinstance(response, str) or isinstance(response, str) or response is None:
        slack_client.api_call(
            'chat.postMessage',
            channel=channel,
            text=response or default_response
        )
    elif (response['text']):
        slack_client.api_call(
            'chat.postMessage',
            channel=response['channel'] if response['channel'] else channel,
            text=response['text']
        )
    else:
        slack_client.api_call(
            'chat.postMessage',
            channel=channel,
            text=response['text'] or default_response,
            attachments=response['attachment']
        )

if __name__ == '__main__':
    if slack_client.rtm_connect(with_team_state=False, auto_reconnect=True):
        print('Stand Up Bot connected and running!')
        # Read bot's user ID by calling web API method `auth.test`
        codereviewbot_id = slack_client.api_call('auth.test')['user_id']
        configure_scheduler()
        while True:
            schedule.run_pending()
            command, channel, sender = parse_bot_commands(slack_client.rtm_read())
            if command:
                handle_command(command, channel, sender)
            time.sleep(RTM_READY_DELAY)
    else:
        print('Connection failed.')
