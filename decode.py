#!/usr/bin/env python
__author__ = "Miguel Krasniqi"

import base64
import json
import logging
import re
from pathlib import Path

from cv2.cv2 import VideoCapture
from pyzbar.pyzbar import decode

import constants
from data.decoders import DecoderType
from data.encoders import EncoderType
from data.encoders_list import ALL_ENCODERS
from data.typing_types import *
from exceptions import DecoderFailed
from utils import split_nth


class BaseUnQRizer:
    @staticmethod
    def _find_encoder(name: str, encoders: Iterable[EncoderType]) -> Optional[EncoderType]:
        for encoder in encoders:
            if encoder.get_encoder_id() == name:
                return encoder
        
        return
    
    @classmethod
    def extract_package(cls, package: str, encoders: Iterable[EncoderType]) -> PackedDataTuple:
        # Extract data
        encoded_data, encoded_information, encoder_string = package.split(constants.DELIMETER)
        data: str = base64.b64decode(encoded_data).decode(constants.ENCODE_TYPE)
        json_information: str = base64.b64decode(encoded_information)
        information: dict = json.loads(json_information)
        encoder: EncoderType = cls._find_encoder(encoder_string, encoders)
        
        if encoder is None:
            raise DecoderFailed(
                f'Couldn`t find the decoder for "{encoder_string}". Try adding more encoders to `encoders`. If '
                f'you passed all encoders, the file might be broken.')
        
        return data, information, encoder
    
    @classmethod
    def get_packages_from_data(
            cls,
            data: str,
            encoders: Iterable[EncoderType] = ALL_ENCODERS,
            skip_error: bool = True
    ) -> Generator[PackedDataTuple, None, None]:
        for package in split_nth(
                data + constants.DELIMETER,  # Adding delimiter because it's removed normally
                constants.DELIMETER,
                re.compile(constants.DATA_STRING_REVERSE).groups
        ):
            try:
                data, information, encoder = cls.extract_package(package, encoders)
            except DecoderFailed as e:
                if skip_error:
                    logging.warning("A package couldn`t be extracted. Here`s the exception: " + str(e))
                    continue
                else:
                    raise e
            
            yield data, information, encoder
    
    @staticmethod
    def decode_qr(opened_image) -> str:
        decoded = decode(opened_image)
        
        return decoded[0].data.decode("utf-8")
    
    @staticmethod
    def _get_video_frames(cap: VideoCapture):
        success, img = cap.read()
        
        while success:
            yield img
            
            success, img = cap.read()
    
    @classmethod
    def get_data_from_video(cls, path: Union[Path, str]) -> str:
        cap = VideoCapture(str(path))
        found = []
        
        for frame in cls._get_video_frames(cap):
            data = cls.decode_qr(frame)
            found.append(data)
        
        return "".join(found)
    
    @staticmethod
    def handle_data(data: str, information: JsonSerializable, decoder: DecoderType):
        instance = decoder(data, information)
        
        instance.handle_data()


class SimpleUnQRizer(BaseUnQRizer):
    @classmethod
    def decode_video(cls, file: Union[Path, str]):
        data = cls.get_data_from_video(file)
        packages = list(cls.get_packages_from_data(data))
        
        for package in packages:
            cls.handle_data(package[0], package[1], package[2].decoder)
