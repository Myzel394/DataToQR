#!/usr/bin/env python
__author__ = "Miguel Krasniqi"

import base64
import json
import re
from fnmatch import fnmatch
from pathlib import Path

import magic

import constants
from checks import is_base64, is_json_serializable
from data.decoders import FileDecoder, TextDecoder
from data.typing_types import *
from exceptions import EncoderError

mime = magic.Magic(mime=True)


class BaseDataEncoderInterface:
    @staticmethod
    def encode_string(data: str) -> str:
        return base64.b64encode(data.encode(constants.ENCODE_TYPE)).decode(constants.ENCODE_TYPE)
    
    def build_qr_data(self, data_opts: Optional[dict] = None, information_opts: Optional[dict] = None) -> str:
        # Constrain values
        if data_opts is None:
            data_opts = {}
        if information_opts is None:
            information_opts = {}
        
        data = self.encode(**data_opts)
        information = self.get_information(**information_opts)
        
        return self.get_qr_data(data, information)
    
    def get_qr_data(self, encoded_value: str, information: JsonSerializable) -> str:
        # Validate
        if not is_base64(encoded_value):
            raise EncoderError(f'The passed `encoded_value` is not in base64!')
        
        if not is_json_serializable(information):
            raise EncoderError(f'The passed `information` is not json serializable!')
        
        json_data = json.dumps(information, separators=(',', ':'))
        information_data = self.encode_string(json_data)
        
        full_data = constants.DATA_STRING.format(data=encoded_value, information=information_data, encoder=self)
        
        return full_data
    
    def get_information(self, **opts) -> JsonSerializable:
        return {}
    
    def encode(self, **opts) -> str:
        """Encodes data into base64 format"""
        raise AssertionError(
            f'The method "{self.__name__}" is missing on "{self.__class__.__name__}" or you used "super().'
            f'{self.__name__}", you are supposed to overwrite this method. You also can`t use this class directly, '
            'it`s only an interface.')
    
    @classmethod
    def get_encoder_id(cls) -> str:
        """
        Returns an unique id for the encoder. The id must follow the regex from "constants.ENCODER_ID_REGEX".
        :return: The id
        """
        name = cls.__name__
        
        if not re.match(constants.ENCODER_ID_REGEX, name):
            raise EncoderError(f'Invalid encoder name for "{cls.__name__}"')
        
        return name
    
    @property
    def encoder_id(self) -> str:
        return self.get_encoder_id()


class FileEncoder(BaseDataEncoderInterface):
    """
    Reads a file and encodes it`s data.
    """
    ENCODES_MIME: Set[str] = {"*/*"}
    decoder = FileDecoder
    
    @classmethod
    def can_encode(cls, file: Union[Path, str]) -> bool:
        try:
            mime_type = mime.from_file(str(file))
        except:
            return False
        
        return any([fnmatch(mime_type, pattern) for pattern in cls.ENCODES_MIME])
    
    def __init__(self, path: Path, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if not path.exists():
            EncoderError(f'Path "{path}" does not exist!')
        
        self.path = path.absolute()
    
    def encode(self, encoding: str = "utf-8") -> str:
        if not self.can_encode(self.path):
            raise EncoderError(
                f'File "{self.path}" can`t be encoded. Probably it`s mime_type is not supported or the file is broken.')
        
        with self.path.open("r", encoding=encoding) as file:
            data = file.read()
        
        return self.encode_string(data)
    
    def get_information(self, encoding: str = "utf-8") -> JsonSerializable:
        return {
            "filename": self.path.name,
            "mime": mime.from_file(str(self.path)),
            "encoding": encoding
        }


class RelativeFileEncoder(FileEncoder):
    def get_information(self, relative_to: Path) -> JsonSerializable:
        data = super().get_information()
        data.update({
            "relative_path": str(self.path.relative_to(relative_to))
        })
        return data


class AbsoluteFileEncoder(FileEncoder):
    def get_information(self) -> JsonSerializable:
        data = super().get_information()
        data.update({
            "absolute_path": str(self.path)
        })
        return data


class TextEncoder(BaseDataEncoderInterface):
    """
    Encodes text.
    """
    decoder = TextDecoder
    
    def __init__(self, text: str, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.text = text
    
    def encode(self, **opts) -> str:
        return self.encode_string(self.text)


EncoderType = Type[BaseDataEncoderInterface]
