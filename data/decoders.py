#!/usr/bin/env python
__author__ = "Miguel Krasniqi"

import logging
from pathlib import Path
from typing import *

from data.typing_types import JsonSerializable
from exceptions import DecoderError
from utils import prompt, read_only_properties


@read_only_properties("information", "data", )
class BaseDataDecoderInterface:
    def __init__(self, data: str, information: JsonSerializable):
        self.data = data
        self.information = information
    
    def handle_data(self):
        pass


class FileDecoder(BaseDataDecoderInterface):
    def handle_data(self):
        # Constrain values
        path = self.information.get("absolute_path") or self.information.get("relative_path")
        if path is None:
            raise DecoderError(f'Path is missing in "{self}"')
        path = Path(path)
        encoding = self.information.get("encoding", "utf-8")
        
        # Permissions check
        if path.exists():
            if not prompt(
                    f'"{self}" wants to create a file that already exists ("{path.absolute()}"). Do you want to '
                    f'proceed?'):
                return
        
        with path.open("w+", encoding=encoding) as file:
            file.write(self.data)


class TextDecoder(BaseDataDecoderInterface):
    def handle_data(self):
        if prompt(f'"{self}" is a simple text decoder. Do you want to export the data into value into a file?'):
            file = input("Filename or path: ")
            path = Path(file)
            with path.open("w", encoding="utf-8") as file_:
                file_.write(self.data)
        else:
            logging.info(self.data)


DecoderType = Type[BaseDataDecoderInterface]
