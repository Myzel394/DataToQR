#!/usr/bin/env python
__author__ = "Miguel Krasniqi"

import logging
import os
import subprocess
import traceback
from multiprocessing import Pool
from pathlib import Path
from typing import *

import qrcode
from PIL import ImageFile
from tqdm import tqdm

import constants
from data.encoders import EncoderType
from data.encoders_list import ALL_ENCODERS, FILE_ENCODERS
from exceptions import EncoderError, EncoderFailed
from utils import pstr, pstrcwd, pstrnone


class BaseQRizer:
    DEFAULT_OPTS = {
        "version": 1,
        "error_correction": qrcode.constants.ERROR_CORRECT_L,
        "border": 0,
        "box_size": 3
    }
    
    DEFAULT_FFMPEG_OPTS = {
        "-framerate", "12",
        "-b:v", "1M",
        "-y"
    }
    
    @staticmethod
    def get_encoded_data(
            targeted: Any,
            encoders: List[EncoderType] = ALL_ENCODERS,
            opts: Optional[dict] = None,
            information_opts: Optional[dict] = None,
            show_traceback: bool = False
    ) -> str:
        for Klaas in encoders:
            instance = Klaas(targeted)
            try:
                data = instance.build_qr_data(opts, information_opts)
            except EncoderError:
                logging.warning(f'Encoder "{Klaas.__name__}" didn`t work.')
                
                if show_traceback:
                    traceback.print_exc()
                
                continue
            else:
                return data
        
        traceback.print_exc()
        raise EncoderFailed(
            f'No working encoder found. Tried {len(encoders)} encoders. You can try using a more generic one.')
    
    @staticmethod
    def split_data(data: str, size: int = constants.DATA_CHUNK_SIZE) -> List[str]:
        return [
            data[i:i + size] for i in range(0, len(data), size)
        ]
    
    @classmethod
    def create_frame(cls, data: str, output: Optional[Path] = None, opts: Optional[dict] = None) -> ImageFile:
        """
        Creates a QR-Code image of the given `data` and saves it as `output`.

        :param data: The data
        :type data: str

        :param output: The path where the file should be saved. If None, !`cwd()/image.png` will be used.
        :type output: str

        :param opts: Options for the qrcode generator
        :type output: dict, optional
        
        :return: ImageFile from qrcode.make_image()
        :rtype: ImageFile
        """
        # Constrain values
        if opts is None:
            opts = {}
        if output is None:
            output = Path.cwd().joinpath("image.png")
        
        # Merge opts
        use_opts = cls.DEFAULT_OPTS.copy()
        use_opts.update(opts)
        
        # Create qr code
        qr = qrcode.QRCode(**use_opts)
        qr.add_data(data)
        
        img = qr.make_image()  # type: ImageFile
        img.save(output)
        return img
    
    @classmethod
    def _create_video_handle_thread(cls, passed: Tuple[str, Path, Optional[dict]]) -> None:
        data, path, opts = passed
        cls.create_frame(data, path, opts)
    
    @classmethod
    def create_video(
            cls,
            data_splitted: List[str],
            output: Optional[Path] = None,
            temp: Optional[Path] = None,
            
            ffmpeg_location: Path = Path("C:\\Program Files\\ffmpeg\\bin\\ffmpeg.exe"),
            ffmpeg_opts: Optional[dict] = None,
            
            threads: Optional[int] = None,
            
            frame_opts: Optional[dict] = None
    ):
        # Constrain values
        CURRENT = Path.cwd()
        
        if output is None:
            output = CURRENT.joinpath("qr_data.avi")
        if temp is None:
            temp = CURRENT.joinpath("temp/")
        if ffmpeg_opts is None:
            ffmpeg_opts = {}
        if threads is None:
            threads = os.cpu_count()
        
        # Merge opts
        use_opts = cls.DEFAULT_FFMPEG_OPTS.copy()
        use_opts.update(ffmpeg_opts)
        
        # Preparation
        # Empty temp folder
        if temp.exists():
            temp.unlink()
        temp.mkdir(exist_ok=True)
        
        # Create frames
        pool_data = [
            (
                data,  # encoded string data
                temp.joinpath(f"image-{i}.png"),  # Image path
                frame_opts  # options
            )
            for i, data in enumerate(data_splitted)
        ]
        with Pool(threads) as pool:
            list(
                tqdm(
                    pool.imap(cls._create_video_handle_thread, pool_data),
                    desc="Creating frames"
                )
            )
        
        # Create video
        subprocess.Popen([
            ffmpeg_location,
            "-i", temp.joinpath("image-%d.png").absolute(),
            *ffmpeg_opts,
            output.absolute()
        ])


class SimpleQRizer(BaseQRizer):
    @classmethod
    def encode_file(
            cls,
            file: Union[Path, str],
            output: Union[Path, str, None] = None,
            encoders: List[EncoderType] = FILE_ENCODERS,
            relative_to: Union[Path, str, None] = None,
            show_traceback: bool = False,
    ):
        # Constrain values
        file = pstr(file)
        output = pstrnone(output)
        relative_to = pstrcwd(relative_to)
        
        information_opts = {
            "relative_to": relative_to
        }
        
        data = cls.get_encoded_data(file, encoders=encoders, information_opts=information_opts,
                                    show_traceback=show_traceback)
        splitted = cls.split_data(data)
        cls.create_video(splitted, output)
