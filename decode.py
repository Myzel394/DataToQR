#!/usr/bin/env python
__author__ = "Miguel Krasniqi"

import json
import logging
import re
from functools import partial
from multiprocessing import Pool
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
from utils import constrain_cap, get_threads, pstr, pstrnone

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
        if raw_package.endswith(remove := constants.DELIMITER):
            raw_package = raw_package.rstrip(remove)
        
        encoded_data, encoded_information, encoder_string = raw_package.split(constants.DELIMITER)
        data: str = encoded_data
        information: JsonSerializable = decode_information(encoded_information)
        
        return data, information, encoder_string
    
    @classmethod
    def raw_to_packed_data(cls, raw: str) -> Generator[PackedDataTupleNotResolved, None, None]:
        """
        Yields raw data to packed data.
        :param raw: The raw data
        """
        # Ignore last split because it`s empty
        if raw.endswith((remove := constants.FULL_DELIMITER)):
            raw = raw.rstrip(remove)
        
        for package in raw.split(constants.FULL_DELIMITER):
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
        found: str = ""
        
        for frame in tqdm(cls._get_video_frames(cap), desc="Reading video", total=frames):
            data = cls.decode_qr(frame)
            found += data
        
        return found
    
    @staticmethod
    def _split_partial_data(
            data: str,
            single_delimiter: str = constants.DELIMITER,
            full_delimiter: str = constants.FULL_DELIMITER,
            regex=data_string_reverse_regex
    ) -> Tuple[DataList, List[str]]:
        found: DataList = []
        remaining = []
        
        if not data.endswith(full_delimiter):
            # If there`s a packed dataset in the data, remove the partial loaded data at the end
            if full_delimiter in data:
                index = data.rfind(full_delimiter)
                temp = data[:index]
            else:
                temp = ""
            remaining.append(data[len(temp):])
            data = temp
        
        for element in data.split(full_delimiter):
            if regex.match(element):
                found.append(element.split(single_delimiter))
            else:
                remaining.append(element)
        
        return found, remaining
    
    @classmethod
    def decode_video_instantly(
            cls,
            *,
            video: Optional[PathStr] = None,
            packed_data_only: bool = True,
            cap: Optional[VideoCapture] = None,
    ) -> Generator[Union[PackedDataTuple, str], str, None]:
        """
        Decodes a video and yields packed data instantly.
        
        :param video: Optional. Path to the video.
        :param packed_data_only: Whether only ready-to-use packed data should be yield.
        :param cap: Optional. VideoCapture instance, if None, one will be created based on `video` path.
        :return: None
        """
        
        def yield_data(ready, value: str):
            if packed_data_only:
                return ready
            else:
                return value
        
        # Constrain values
        cap = constrain_cap(video, cap)
        
        found: str = ""
        
        # Iterate over all frames and decode its data. Then get the ready-to-use data and the partial loaded data.
        # Yield the ready-to-use data if `packed_data_only` is True, otherwise yield the raw found data so far.
        for frame in cls._get_video_frames(cap):
            # Get data
            data = cls.decode_qr(frame)
            found += data
            
            # Get ready-to-use and partial loaded data
            ready_data, new_found = cls._split_partial_data(found)
            yield yield_data(ready_data, found)
            found = "".join(new_found)
        
        yield yield_data(cls._split_partial_data(found)[0], found)
    
    @classmethod
    def _handle_video_instantly_thread(cls, data_list: DataList, skip_error: bool = True, **kwargs):
        def handle_now(given_data: list):
            cls.handle_raw_data(constants.DELIMITER.join(given_data) + constants.DELIMITER, **kwargs)
        
        for data in data_list:
            try:
                handle_now(data)
            except Exception as e:
                if skip_error:
                    logging.warning(
                        "There was an error while handling some data. Original exception: " + str(e)
                    )
                else:
                    raise e
    
    @classmethod
    def handle_video_instantly(
            cls,
            video: Optional[PathStr] = None,
            *,
            skip_error: bool = True,
            cap: Optional[VideoCapture] = None,
            threads: Optional[int] = None,
            **kwargs
    ) -> None:
        """Decodes a video and handles instantly. If you want to decode a video and handle its data, use this. No
        data will be returned."""
        
        # Constrain values
        cap = constrain_cap(video, cap)
        threads = get_threads(threads)
        
        # Video
        frames = int(cap.get(CAP_PROP_FRAME_COUNT))
        
        with Pool(threads) as pool:
            # Arguments pass method by: https://stackoverflow.com/a/39366868/9878135
            list(
                tqdm(
                    pool.imap(
                        partial(cls._handle_video_instantly_thread, **{
                            "skip_error": skip_error,
                            **kwargs
                        }),
                        cls.decode_video_instantly(cap=cap)
                    ),
                    desc="Handling video",
                    total=frames
                )
            )


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
