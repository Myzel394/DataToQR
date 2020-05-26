#!/usr/bin/env python
__author__ = "Miguel Krasniqi"

import json
import logging
import re
from operator import itemgetter

from cv2.cv2 import CAP_PROP_FRAME_COUNT, VideoCapture
from pyzbar.pyzbar import decode
from tqdm import tqdm

import constants
from data.decoders import DecoderType
from data.encoders import EncoderType
from data.encoders_list import ALL_ENCODERS
from exceptions import DecoderFailed
from information import decode_information
from typing_types import *
from utils import pstr, pstrnone, rstrip_until, split_nth

data_string_reverse_regex = re.compile(constants.DATA_STRING_REVERSE)


class BaseDataExtractor:
    @staticmethod
    def _find_encoder(name: str, encoders: Iterable[EncoderType]) -> EncoderType:
        """
        Finds the encoder with a given id `name`

        :param name: The id name
        :param encoders: For what encoders should be searched

        :return: The encoder

        :raises:
            DecoderFailed: No encoder found
        """
        for encoder in encoders:
            if encoder.get_encoder_id() == name:
                return encoder
        
        raise DecoderFailed(
            f'Couldn`t find the encoder for "{name}".... Try adding more encoders to `encoders`. If '
            f'you passed all encoders, the file might be broken.')
    
    @classmethod
    def extract_package(cls, raw_package: str) -> PackedDataTupleNotResolved:
        """Extracts a raw_package into packed data"""
        # Extract data
        encoded_data, encoded_information, encoder_string, _ = raw_package.split(constants.DELIMITER)
        data: str = encoded_data
        information: JsonSerializable = decode_information(encoded_information)
        
        return data, information, encoder_string
    
    @classmethod
    def raw_to_packed_data(cls, raw: str) -> Generator[PackedDataTupleNotResolved, None, None]:
        """
        Yields raw data to packed data.
        :param raw: The raw data
        """
        for package in split_nth(
                raw,
                constants.DELIMITER,
                re.compile(constants.DATA_STRING_REVERSE).groups,
                True
        ):
            yield cls.extract_package(package)
    
    @classmethod
    def packed_to_package(
            cls,
            package: Union[PackedDataTuple, PackedDataTupleNotResolved],
            encoders: Iterable[EncoderType] = ALL_ENCODERS
    ) -> Dict[str, Any]:
        """Converts packed data (Tuple[raw, information, encoder]) to a dict"""
        data, information, encoder = package
        
        if type(encoder) is str:
            encoder = cls._find_encoder(encoder, encoders)
        
        return {
            "data": data,
            "information": information,
            "encoder": encoder
        }
    
    @classmethod
    def get_packages_from_raw(
            cls,
            data: str,
            encoders: Iterable[EncoderType] = ALL_ENCODERS,
    ) -> Generator[Dict[str, Any], None, None]:
        """Yields all packages for raw data."""
        for package in cls.raw_to_packed_data(data):
            yield cls.packed_to_package(package, encoders)


class HandleDataExtractor(BaseDataExtractor):
    """
    Handles data. I.e. A FileEncoder will write data.
    """
    
    @classmethod
    def handle_raw_data(cls, data: str, encoders: Iterable[EncoderType] = ALL_ENCODERS, **kwargs):
        """Handles raw, encoded data"""
        packed_data = cls.get_packages_from_raw(data, encoders=encoders)
        cls.handle_packed_data(packed_data, **kwargs)
    
    @staticmethod
    def handle_ready_data(data: str, information: JsonSerializable, decoder: DecoderType, **kwargs) -> None:
        """Handles ready-to-use data (pure data, information object, decoder class)"""
        instance = decoder(data, information)
        instance.handle_data(**kwargs)
    
    @classmethod
    def handle_packed_data(cls, packed: Iterable[Dict[str, Any]], **kwargs) -> None:
        """Handles packages. Also shows a tqdm progressbar"""
        for single_data in packed:
            data, information, encoder = itemgetter("data", "information", "encoder")(single_data)
            cls.handle_ready_data(data, information, encoder.decoder, **kwargs)
    
    @classmethod
    def handle_video(
            cls,
            file: PathStr,
            encoders: Iterable[EncoderType] = ALL_ENCODERS,
            **kwargs
    ) -> None:
        """Decodes data first and handles it then"""
        data = cls.decode_video(file)
        cls.handle_raw_data(data, encoders=encoders, **kwargs)
    
    @classmethod
    def handle_json_file(
            cls,
            file: PathStr,
            encoding: str = "utf-8",
            encoders: Iterable[EncoderType] = ALL_ENCODERS,
            **kwargs
    ) -> None:
        """Handles a json-file"""
        file = pstr(file)
        
        with file.open("r", encoding=encoding) as file:
            packages = json.load(file)
        
        found = []
        
        for package in packages:
            # Get values
            data, information, encoder = itemgetter("data", "information", "encoder")(package)
            encoder = cls._find_encoder(encoder, encoders=encoders)
            found.append({
                "data": data,
                "information": information,
                "encoder": encoder
            })
        
        cls.handle_packed_data(found, **kwargs)
    
    @staticmethod
    def decode_qr(opened_image) -> str:
        """Decodes a qr-code and returns it`s data"""
        decoded = decode(opened_image)
        
        return decoded[0].data.decode("utf-8")
    
    @staticmethod
    def _get_video_frames(cap: VideoCapture):
        success, img = cap.read()
        
        while success:
            yield img
            
            success, img = cap.read()
    
    @classmethod
    def decode_video(cls, path: PathStr) -> str:
        """Decodes a video and returns it`s data"""
        # Constrain values
        path = pstr(path)
        
        # Video
        cap = VideoCapture(str(path))
        frames = int(cap.get(CAP_PROP_FRAME_COUNT))
        found: List[str] = []
        
        for frame in tqdm(cls._get_video_frames(cap), desc="Reading video", total=frames):
            data = cls.decode_qr(frame)
            found.append(data)
        
        return "".join(found)
    
    @staticmethod
    def _split_partial_data(
            data: str,
            single_delimiter: str = constants.DELIMITER,
            full_delimiter: str = constants.FULL_DELIMITER,
            regex=data_string_reverse_regex
    ) -> Tuple[List[List[str]], List[str]]:
        found: List[List[str]] = []
        remaining = []
        
        if not data.endswith(full_delimiter):
            try:
                temp = rstrip_until(data, full_delimiter)
            except ValueError:
                pass
            else:
                remaining.append(data[len(temp)])
                data = temp
        
        for element in data.split(full_delimiter):
            if regex.match(element):
                found.append(element.split(single_delimiter))
            else:
                remaining.append(element)
        
        return found, remaining
    
    @classmethod
    def handle_video_instantly(
            cls,
            path: PathStr,
            skip_error: bool = True,
            **kwargs
    ) -> None:
        """Decodes a video and handles instantly. If you want to decode a video and handle its data, use this. No
        data will be returned. Only works with like 95% of the data. I`m still searching for a solution, if you know
        one please tell me."""
        
        def handle_now(given_data: list):
            cls.handle_raw_data(constants.DELIMITER.join(given_data) + constants.DELIMITER, **kwargs)
        
        # Constrain values
        path = pstr(path)
        
        # Video
        cap = VideoCapture(str(path))
        frames = int(cap.get(CAP_PROP_FRAME_COUNT))
        handle_every = re.compile(constants.DATA_STRING_REVERSE).groups
        found: List[str] = []
        
        for frame in tqdm(cls._get_video_frames(cap), desc="Handling video", total=frames):
            data = cls.decode_qr(frame)
            found.append(data)
            
            # Handle and reset
            use_data, new_found = cls._split_partial_data("".join(data))
            for single_data in use_data:
                try:
                    handle_now(single_data)
                except Exception as e:
                    if skip_error:
                        logging.warning(
                            "There was an error while handling some data. Original exception: " + str(e)
                        )
                        continue
                    raise e
            found = [x + constants.FULL_DELIMITER for x in new_found]
        
        handle_now(found)


class DumpDataExtractor(BaseDataExtractor):
    @classmethod
    def get_json(
            cls,
            data: Union[str, PackedDataTupleNotResolved, Dict[str, Any]],
            *,
            minify: bool = True
    ) -> str:
        data_type = type(data)
        
        object_data: List[Dict[str, Union[JsonSerializable, EncoderType]]]
        
        if data_type is str:
            object_data = [cls.packed_to_package(x) for x in cls.raw_to_packed_data(data)]
        elif data_type is dict:
            object_data = [data]
        elif data_type is tuple:
            object_data = [cls.packed_to_package(data)]
        elif data_type is list:
            object_data = data
        else:
            raise DecoderFailed(f'Given data type can`t be dumped to json.')
        
        for dct in object_data:
            dct["encoder"] = dct["encoder"].get_encoder_id()
        
        if minify:
            json_kwargs = {"separators": (",", ":")}
        else:
            json_kwargs = {"indent": 4}
        
        return json.dumps(object_data, **json_kwargs)
    
    @classmethod
    def dump_to_json(
            cls,
            data: Union[str, PackedDataTupleNotResolved, Dict[str, Any]],
            file: Optional[PathStr] = None,
            *,
            encoding: str = "utf-8",
            **kwargs
    ):
        # Constrain values
        file = pstrnone(file)
        if file is None:
            file = Path.cwd().joinpath("data.json")
        json_data = cls.get_json(data, **kwargs)
        
        with file.open("w", encoding=encoding) as file:
            file.write(json_data)
