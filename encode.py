#!/usr/bin/env python
__author__ = "Miguel Krasniqi"

import logging
import os
import shutil
import subprocess
import traceback
from itertools import chain
from multiprocessing import Pool
from pathlib import Path
from typing import *

import qrcode
from PIL import ImageFile
from tqdm import tqdm

import constants
from data.encoders import EncoderType
from data.encoders_list import ALL_ENCODERS
from exceptions import EncoderError, EncoderFailed
from typing_types import Kwargs, PathStr
from utils import create_temp, get_skip_files, pstr, pstrnone


class BaseDataInsertor:
    @staticmethod
    def get_encoded_data(
            targeted: Any,
            *,
            encoders: Iterable[EncoderType] = ALL_ENCODERS,
            opts: Optional[dict] = None,
            information_opts: Optional[dict] = None,
            show_traceback: bool = False
    ) -> str:
        """
        Tries to encode by using `encoders`. Tries encoders one-by-one until one successfully works.
        The returned data gets returned.
        
        :param targeted: The value for the init function of the encoder class.
        :param encoders: An iterable of encoders that should be tried. NOTE: Order is important!
        :param opts: Options for the `build_qr_data` method.
        :param information_opts: Information options for the `build_qr_data` method.
        :param show_traceback: Should a traceback be shown when an encoder didn't work? NOTE: If no encoder worked,
        a traceback will always be shown.
        :return: The encoded value
        """
        for Klaas in encoders:
            try:
                # noinspection PyArgumentList
                instance = Klaas(targeted)
                data = instance.build_qr_data(opts, information_opts)
            except EncoderError:
                logging.warning(f'There`s an {EncoderError.__name__} error with "{Klaas.__name__}"')
                
                if show_traceback:
                    traceback.print_exc()
                
                continue
            except:
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
        """Splits data into smaller parts"""
        return [
            data[i:i + size] for i in range(0, len(data), size)
        ]


class VideoDataInsertor(BaseDataInsertor):
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
        use_opts = constants.DEFAULT_OPTS.copy()
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
    def create_frames(
            cls,
            data: List[str],
            threads: Optional[int] = None,
            frame_opts: Optional[Kwargs] = None,
            temp: Optional[PathStr] = None,
            skip_existing: bool = True,
            file_regex: str = "image-([\\d]+).png"
    ):
        # Constrain values
        if threads is None:
            threads = os.cpu_count()
        if frame_opts is None:
            frame_opts = {}
        temp = create_temp(temp)
        if skip_existing:
            skip = get_skip_files(file_regex, temp, "*.png")
        else:
            skip = set()
        
        pool_data = [
            (
                data,  # encoded string data
                temp.joinpath(f"image-{i}.png"),  # Image path
                frame_opts,  # options,
            )
            for i, data in enumerate(data)
            if str(i) not in skip
        ]
        
        logging.info(f'Using {threads} Threads to create frames.')
        with Pool(threads) as pool:
            list(
                tqdm(
                    pool.imap(cls._create_video_handle_thread, pool_data),
                    desc="Creating frames",
                    total=len(pool_data)
                )
            )
    
    @classmethod
    def create_video(
            cls,
            data_or_split: Union[List[str], str],
            output: Optional[Path] = None,
            *,
            temp: Optional[PathStr] = None,
            clear_temp: bool = False,
            
            ffmpeg_location: Path = Path("C:\\Program Files\\ffmpeg\\bin\\ffmpeg.exe"),
            ffmpeg_opts: Optional[dict] = None,
            
            **kwargs,
    ):
        """
        Creates a video of QR-Codes using `data_or_split`.
        :param data_or_split: Either already split data or pure string data. If str, it will be split.
        :param output:
        :param temp:
        :param clear_temp:
        :param ffmpeg_location:
        :param ffmpeg_opts:
        :return:
        """
        # Constrain values
        if type(data_or_split) is str:
            data = cls.split_data(data_or_split)
        elif type(data_or_split) is list:
            data = data_or_split
        else:
            raise EncoderFailed(f'The given data can`t be used. It must be either str or a list containing strings!')
        CURRENT = Path.cwd()
        if output is None:
            output = CURRENT.joinpath("qr_data.avi")
        if temp is None:
            temp = CURRENT.joinpath("temp/")
        if ffmpeg_opts is None:
            ffmpeg_opts = {}
        
        # Merge opts
        use_opts = constants.DEFAULT_FFMPEG_OPTS.copy()
        use_opts.update(ffmpeg_opts)
        use_opts = list(chain.from_iterable(use_opts.items()))
        
        # Preparation
        # Empty temp folder
        if clear_temp:
            if temp.exists():
                shutil.rmtree(str(temp))
            temp.mkdir()
        # Empty file
        if output.exists():
            output.unlink()
        
        # Create frames
        cls.create_frames(data=data, temp=temp, **kwargs)
        
        # Create video
        logging.warning("The video will be created now using ffmpeg, wait until it is finished before opening it!")
        
        process = subprocess.Popen([
            ffmpeg_location,
            "-i", temp.joinpath("image-%d.png").absolute(),
            *use_opts,
            output.absolute()
        ])
        process.communicate()


class FileDataInsertor(VideoDataInsertor):
    @classmethod
    def collect_data_from_files(
            cls,
            files: Iterable[PathStr],
            **kwargs
    ) -> Generator[str, None, None]:
        """Yields encoded data of the files"""
        for file in files:
            yield cls.get_encoded_data(
                file,
                **kwargs
            )
    
    @classmethod
    def encode_multiple_files(
            cls,
            files: Iterable[PathStr],
            output: Optional[PathStr] = None,
            **kwargs
    ) -> str:
        # Constrain values
        data = "".join(list(cls.collect_data_from_files(files, **kwargs)))
        
        cls.create_video(data, output)
        
        return data
    
    @classmethod
    def encode_multiple(
            cls,
            targets: Iterator[PathStr],
            output: Optional[PathStr] = None,
            **kwargs
    ) -> str:
        # Constrain values
        targets: List[Path] = list(map(lambda x: pstr(x), targets))
        
        # Collect data
        data = []
        for target in tqdm(targets, desc="Collection data", total=len(targets)):
            if target.is_dir():
                temp = cls.encode_folder(target, **kwargs)
            else:
                temp = cls.encode_file(target, **kwargs)
            
            data.append(temp)
        
        data = "".join(data)
        
        cls.create_video(data, output)
        
        return data
    
    @classmethod
    def encode_file(
            cls,
            file: PathStr,
            output: Optional[PathStr] = None,
            **kwargs
    ) -> str:
        # Constrain values
        file = pstr(file)
        
        data = cls.get_encoded_data(
            file,
            **kwargs
        )
        
        cls.create_video(data, output)
        
        return data
    
    @classmethod
    def encode_folder(
            cls,
            folder: PathStr,
            output: Optional[PathStr] = None,
            *,
            folder_glob: str = "*",
            recursive: bool = True,
            **kwargs,
    ) -> str:
        # Constrain values
        folder = pstr(folder)
        output = pstrnone(output)
        information_opts = kwargs.pop("information_opts", {})
        if (key := "relative_to") not in information_opts:
            information_opts[key] = folder.parent.absolute()
        
        # Get values
        method = folder.rglob if recursive else folder.glob
        # Folders don`t need to be encoded, because the path will be saved
        files = {x for x in method(folder_glob) if x.is_file()}
        
        return cls.encode_multiple_files(
            files, output,
            information_opts=information_opts,
            **kwargs
        )


class TextDataInsertor(VideoDataInsertor):
    @classmethod
    def encode_text(cls, text: str, output: Optional[PathStr] = None, **kwargs) -> str:
        data = cls.get_encoded_data(
            text,
            **kwargs
        )
        return cls.create_video(data, output)
    
    @classmethod
    def encode_text_from_file(
            cls,
            path: str,
            output: Optional[PathStr] = None,
            *,
            encoding: str = "utf-8",
            **kwargs) -> str:
        # Constrain values
        path = pstr(path)
        
        with path.open("r", encoding=encoding) as file:
            data = file.read()
        
        return cls.encode_text(data, output, **kwargs)
