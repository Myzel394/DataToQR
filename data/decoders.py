#!/usr/bin/env python
__author__ = "Miguel Krasniqi"

import base64
import logging
from pathlib import Path
from typing import *

import constants
from data.typing_types import JsonSerializable, PathStr
from exceptions import DecoderError
from utils import prompt, pstr, read_only_properties


@read_only_properties("information", "data", )
class BaseDataDecoderInterface:
    @staticmethod
    def get_data(raw: str) -> Any:
        return base64.b64decode(raw).decode(constants.ENCODE_TYPE)
    
    def __init__(self, raw_data: str, information: JsonSerializable):
        self.data = self.get_data(raw_data)
        self.information = information
    
    def handle_data(self, *, log: bool = False):
        pass


class FileDecoder(BaseDataDecoderInterface):
    def handle_data(self, *, log: bool = False, ignore_perms: bool = False, base_path: Optional[PathStr] = None):
        # Constrain values
        path = self.information.get("path")
        if path is None:
            raise DecoderError(f'Path is missing in "{self}"')
        path = Path(path)
        encoding = self.information.get("encoding", "utf-8")
        
        # Permissions check
        if not ignore_perms and path.exists():
            # File already exists
            if not prompt(
                    f'"{self}" wants to create a file that already exists ("{path.absolute()}"). Do you want to '
                    f'proceed?'):
                return
        
        if not path.is_absolute():
            # File is relative
            if base_path is not None:
                base = pstr(base_path)
            else:
                if not ignore_perms:
                    base = self.prompt_path(path)
                else:
                    base = Path.cwd()
            
            path = base.joinpath(str(path)[1:])
        
        # Create file and write data
        path.parent.mkdir(exist_ok=True, parents=True)
        with path.absolute().open("w", encoding=encoding) as file:
            file.write(self.data)
        
        if log:
            logging.info(f'Created file "{str(path.relative_to(base))}"')
    
    @staticmethod
    def validate_path(input: str) -> Optional[Path]:
        if input == "":
            return Path.cwd()
        if (base := Path(input)).exists():
            return base
        return None
    
    def prompt_path(self, path: PathStr) -> Path:
        string = input(f'"{self}" want`s to create a file with a relative path (relative path: "{str(path)}"). '
                       f'Please provide a base path, otherwise the current working directory (cwd) will be '
                       f'used.')
        base = self.validate_path(string)
        
        while base is None:
            string = input("Please provide an existing path. ")
            
            base = self.validate_path(string)
        
        return path


class TextDecoder(BaseDataDecoderInterface):
    DEFAULT_FILE_NAME = "data.txt"
    
    def handle_data(self, *, log: bool = False):
        if prompt(f'"{self}" is a simple text decoder. Do you want to export the data into a file? Otherwise the '
                  f'value will be printed to console.'):
            file = input(f'Filename or path (None for "{self.DEFAULT_FILE_NAME}"): ')
            
            if file == "":
                file = self.DEFAULT_FILE_NAME
            
            path = Path(file)
            with path.open("w", encoding="utf-8") as file_:
                file_.write(self.data)
        else:
            logging.info("Here`s the value printed:")
            logging.info(self.data)


class BytesDecoder(FileDecoder):
    @staticmethod
    def get_data(raw: str) -> Any:
        return raw
    
    def handle_data(self, *, encoding: str = "utf-8", log: bool = False):
        data = base64.b64decode(bytes(self.data, encoding))
        
        # Constrain values
        path = self.information.get("path")
        if path is None:
            raise DecoderError(f'Path is missing in "{self}"')
        path = Path(path)
        
        with path.open("wb") as file:
            file.write(data)


DecoderType = Type[BaseDataDecoderInterface]
