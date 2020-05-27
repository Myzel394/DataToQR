#!/usr/bin/env python
__author__ = "Miguel Krasniqi"

import base64
import logging
from datetime import date
from pathlib import Path
from typing import *

import constants
from exceptions import DecoderError
from typing_types import JsonSerializable, PathStr
from utils import pstrcwd, read_only_properties


@read_only_properties("information", "data", "__raw_data")
class BaseDataDecoderInterface:
    @staticmethod
    def get_data(raw: str) -> Any:
        return base64.b64decode(raw).decode(constants.ENCODE_TYPE)
    
    def __init__(self, raw_data: str, information: JsonSerializable):
        self.__raw_data = raw_data
        self.data = self.get_data(raw_data)
        self.information = information
    
    def __repr__(self) -> str:
        return f'<{self.__class__.__name__} with raw="{self.__raw_data[:20]}"...>'
    
    def handle_data(self, *, log: bool = False, **_) -> None:
        pass


class FileDecoder(BaseDataDecoderInterface):
    def write_action(self, path, **kwargs):
        encoding = self.information.get("encoding", "utf-8")
        
        with path.open("w", encoding=encoding) as file:
            file.write(self.data)
    
    def handle_data(self, *, log: bool = False, base_path: Optional[PathStr] = None, **_):
        # Constrain values
        path = self.information.get("path")
        if path is None:
            raise DecoderError(f'Path is missing in "{self}"')
        path = Path(path)
        
        if not path.is_absolute():
            if not base_path:
                base_path = Path.cwd()
            path = base_path.joinpath(str(path)[1:])
        path.parent.mkdir(exist_ok=True, parents=True)
        
        # Create file and write data
        self.write_action(path, log=log)
        
        if log:
            if base_path is not None:
                logging.info(f'Created file "{str(path.relative_to(base_path))}"')


class TextDecoder(BaseDataDecoderInterface):
    def get_filepath(self, base_path: Path) -> Path:
        base = f"QR-Data from {date.today().strftime('%d.%m.%Y')}{{}}.txt"
        filename = base.format("")
        counter = 1
        
        while True:
            path = base_path.joinpath(filename)
            
            if path.exists():
                filename = base.format(f" ({counter})")
                counter += 1
            else:
                return path
    
    def handle_data(self, *, log: bool = False, base_path: Optional[PathStr] = None, write_file: bool = True, **_):
        # Constrain values
        base_path = pstrcwd(base_path)
        
        if write_file:
            path = self.get_filepath(base_path)
            
            with path.open("w", encoding="utf-8") as file_:
                file_.write(self.data)
        else:
            logging.info("Here`s the QR-Data printed:")
            logging.info(self.data)


class BytesDecoder(FileDecoder):
    @staticmethod
    def get_data(raw: str) -> Any:
        return raw
    
    def write_action(self, path, encoding: str = "utf-8", **kwargs):
        data = base64.b64decode(bytes(self.data, encoding))
        
        with path.open("wb") as file:
            file.write(data)


DecoderType = Type[BaseDataDecoderInterface]
