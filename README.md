# ACJBot
Slack bot for creating standup order

# [Environment Setup](https://www.fullstackpython.com/blog/build-first-slack-bot-python.html)
1. Open your terminal and navigate to the ACJBot directory
2. Type `virtualenv starterbot` (you can replace `starterbot` with whatever you want your virtual environment to be called; it's not important)
   * You may need to install this command - on WSL, I needed to run `sudo apt install python3-virtualenv`
3. Activate the virtual environment with `starterbot/bin/activate` (again, replace `starterbot` with whatever you decided to name your virtual environment)
4. Install requirements: `pip install -r requirements.txt`
5. Export your slack token: `export SLACK_BOT_TOKEN='(bot user access token)'`

Now (in theory) you can run the bot locally with `python3 main.py` or `py main.py` depending on what version is being run.

## Features
All commands take input separated by a single space character. Fields that are italicized are optional.
Currently the commands supported are as follows:

showtable *`<str>`*:
- shows the standup table, if an argument is given, it will return the standup table with the corresponding name

droptable *`<str>`*:
- clears the standup table, if an argument is given, it will clear the standup table with the corresponding name

add *`<str>`* `<@user>...`:
- adds the mentioned users to the standup table, if the string argument is given, it will add the users to the corresponding table

remove `<@user>`:
- removes the mentioned user from the standup table
- future patch to remove from specific tables

sort `<SortType> <Option>`:
- performs the sorting with the SortType specified, user field for volunteering is optional
- future patch to remove from specific tables

help:
- brings up a list of all of the functions that the bot supports

addteam `<str>`:
- creates a new team with the name specified

showteams:
- lists out all of the current active teams

removeteam `<str>`:
- deletes the team with the name specified if it exists

clearteams:
- coming in a future patch

psconfig `<str>`:
- 24-hr time: configures postscrum message for the channel to be sent at the time specified
- 'stop': removes current configuration

advice:
- generates advice

number:
- generates a cool fact about a random number

### SortTypes
alpha
- creates standup order in alphabetical order

ralpha
- creates standup order in reverse alphabetical order

length
- creates standup order based on the length of the username (asc)

random
- creates a random standup order

### Options
pickme
- volunteer yourself to go first

last
- put yourself last on the list

`<@user>`
- select a user to go first
