# StandupBot
Slack bot for creating standup order

# [Environment Setup](https://www.fullstackpython.com/blog/build-first-slack-bot-python.html)
1. Open your terminal and navigate to the ACJBot directory
2. Type `virtualenv starterbot` (you can replace `starterbot` with whatever you want your virtual environment to be called; it's not important)
   * You may need to install this command - on WSL, I needed to run `sudo apt install python3-virtualenv`
3. Activate the virtual environment with `source starterbot/bin/activate` (again, replace `starterbot` with whatever you decided to name your virtual environment)
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
   - `show`: lists the teams that are currently backed up
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
