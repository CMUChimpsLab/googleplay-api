# separator used by search.py, categories.py, ...
SEPARATOR = ";"

LANG            = "en_US" # can be en_US, fr_FR, ...
ANDROID_ID      = "" # "xxxxxxxxxxxxxxxx"
GOOGLE_LOGIN    = "" # "username@gmail.com"
GOOGLE_PASSWORD = ""
AUTH_TOKEN      = None # "yyyyyyyyy"

# Support for rotating among multiple different Google accounts
# Each account must have a corresponding android id, password, and token
ANDROID_ID_S = ["" , "" ] # ["...", "...", ...]
GOOGLE_LOGIN_S = [ "", "" ] # ["user1@gmail.com", "user2@gmail.com" , ...]
GOOGLE_PASSWORD_S = [ "", ""]
AUTH_TOKEN_S = [ None, None ]

# force the user to edit this file
if any([each == None for each in [ANDROID_ID, GOOGLE_LOGIN, GOOGLE_PASSWORD]]):
    raise Exception("config.py not updated")

# Check we have the same number of accounts and ids
cnt = len(ANDROID_ID_S)
if not(cnt == len(GOOGLE_LOGIN_S) and cnt == len(GOOGLE_PASSWORD_S) and cnt == len(AUTH_TOKEN_S)):
    raise Exception("config.py has different number of accounts")

