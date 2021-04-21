# StandupBot
This slack bot helps out with standup meetings via storing teams, sending postscrum messages, and choosing standup orders!

# Getting Access
1. Make sure that you have collaborater permissions to access [the slack app](https://api.slack.com/apps/A01UA2U1Q75) - if you don't have this position, ask Mike.
2. Install Python 3, `pip`, and `virtualenv` if you don't already have them.
3. Clone the repository.
4. Create a .env file and add the line `SLACK_BOT_TOKEN="<Token>"`, with `<Token>` being replaced by the Bot User Oauth Token found on [this page](https://api.slack.com/apps/A01UA2U1Q75/install-on-team?)

# [Environment Setup](https://www.fullstackpython.com/blog/build-first-slack-bot-python.html)
1. Open your terminal and navigate to the standup-slackbot directory
2. Type `virtualenv venv` to make a virtual environment called "venv"
3. Activate the virtual environment with `source venv/bin/activate`
4. Install requirements: `pip install -r requirements.txt`
5. Export your slack token: `export SLACK_BOT_TOKEN='(bot user access token)'`

You can now run the bot locally with `python main.py` or `py main.py`.

## Features
All commands take input separated by a single space character. Fields that are italicized are optional.
Currently the commands supported are as follows:

show `<team>`:
- prints a list of the members (with indicators if they have postscrum) in the specified team if it exists

add `<team>` `@<user>...`:
- adds all mentioned users to the specified team if it exists

remove `<team> @<user>`:
- removes the mentioned user from the specified team

showteams:
- prints a list of all existing teams

addteam `<team>`:
- creates a new team with the name specified if it does not currently exist

removeteam `<team>`:
- deletes the team with the name specified if it exists

backup `<option>`:
- manages the backup file
- Options:
   - `showteams`: lists the teams that are currently backed up
   - `show <team>`: shows a specific team's backup settings 
   - `add <team>`: adds the specified team to the backup file
   - `restore <team>`: restores the specified team from the backup file
   - `remove <team>`: removes the specified team from the backup file

sort `<team> <SortType> <option>`:
- sorts the members of the specified team (based on username)
- SortTypes:
   - `alpha`: alphabetical order
   - `ralpha`: reverse alphabetical order
   - `length`: length (ascending)
   - `rlength`: length (descending)
   - `random`: random
- Options:
   - `pickme`: moves the sender to the front of the list
   - `last`: moves the sender to the back of the list
   - `@<user>`: moves the specified user to the front of the list
- adds postscrum indicators to users that have reacted to their team's postscrum message

ps `<team>` `<option>`:
- configures daily postscrum messages (weekdays) for the channel in which the command is sent
- Options:
   - `time` `<24-hr time>`: sets the time the message to be sent
   - `message` `<message>`: sets the text of the message to be sent
   - `stop`: removes current configuration
- users should react to the message if they have postscrum

advice:
- generates advice

number:
- generates a cool fact about a random number

help:
- brings up a list of all of the functions that the bot supports
