# separator used by search.py, categories.py, ...
SEPARATOR = ";"

LANG            = "en_US" # can be en_US, fr_FR, ...
ANDROID_ID      = "3d716411bf8bc802" # "xxxxxxxxxxxxxxxx"
GOOGLE_LOGIN    = "" # "username@gmail.com"
GOOGLE_PASSWORD = ""
AUTH_TOKEN      = "yQTpxgF0TaObpaIDc7sFxffkUbqn1VgPMa4PfUHAWURWFYrGOflioBgL3ay9psB9PxY6cw."

# force the user to edit this file
if any([each == None for each in [ANDROID_ID, GOOGLE_LOGIN, GOOGLE_PASSWORD]]):
    raise Exception("config.py not updated")

