# separator used by search.py, categories.py, ...
SEPARATOR = ";"

LANG            = "en_US" # can be en_US, fr_FR, ...
ANDROID_ID      = "35A8EE3228915E59" # "xxxxxxxxxxxxxxxx"
GOOGLE_LOGIN    = "newellsimonhall1@gmail.com" # "username@gmail.com"
GOOGLE_PASSWORD = "nsh12345"
AUTH_TOKEN      = None # "yyyyyyyyy"

# force the user to edit this file
if any([each == None for each in [ANDROID_ID, GOOGLE_LOGIN, GOOGLE_PASSWORD]]):
    raise Exception("config.py not updated")

