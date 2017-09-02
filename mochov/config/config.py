import configparser
import os

config_file = os.path.join(os.path.dirname(os.path.abspath(__file__)), "config.ini")

discord_grp = "DISCORD"
token_key = "Token"
prefix_key = "CommandPrefix"


class Config:
    def __init__(self):
        self.config = configparser.RawConfigParser()
        self.read_config()

    def read_config(self):
        if os.path.isfile(config_file):
            self.config.read(config_file)
            return

        self.config[discord_grp] = {}
        self.config[discord_grp][token_key] = ""
        self.config[discord_grp][prefix_key] = "%"

        with open(config_file, "w") as f:
            self.config.write(f)

    @property
    def discord_token(self):
        return self.config[discord_grp][token_key]

    @property
    def discord_prefix(self):
        return self.config[discord_grp][prefix_key]
