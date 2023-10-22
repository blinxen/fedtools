import os
from pathlib import Path
import tomllib
from fedtools.utils import Colors


FEDTOOLS_CONFIG_FILE = os.path.join(Path.home(), ".config/fedtools.toml")


class Config:
    def __init__(self):
        self.__config = None

        if not os.path.exists(FEDTOOLS_CONFIG_FILE):
            print(Colors.RED + "Configuration file does not exist!!" + Colors.RESET)
            exit(1)

        with open(FEDTOOLS_CONFIG_FILE, "rb") as f:
            try:
                self.__config = tomllib.load(f)
            except tomllib.TOMLDecodeError:
                print(
                    Colors.RED
                    + "Configuration file has an invalid format!!"
                    + Colors.RESET
                )
                exit(1)

    def command_config(self, command_name) -> dict:
        """Return command specific configuration from the config file

        Parameters:
            command_name: Command name for which the configuration should be retrieved

        Returns: Command configuration in the form of a dictionary
        """
        return self.__config.get(command_name)
