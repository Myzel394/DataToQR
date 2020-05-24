#!/usr/bin/env python
__author__ = "Miguel Krasniqi"

import argparse
import json
import logging
import os
from pathlib import Path

from decode import DumpDataExtractor, HandleDataExtractor
from typing_types import Kwargs

AVAILABLE_METHODS = {
    "HANDLE": "handle",
    "DUMP": "dump",
    "REVIEW": "review"
}
DEFAULT_AVAILABLE_METHODS = AVAILABLE_METHODS["HANDLE"]


def create_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Encode data into a video of QR-Codes.")
    parser.add_argument(
        "video",
        type=str,
        help="Path to the video",
    )
    parser.add_argument(
        "-m", "--method",
        type=str,
        help=f'What should be done with the data? Available methods: ' +
             ', '.join([f'"{value}"' for value in AVAILABLE_METHODS.values()]) +
             f'default: "{DEFAULT_AVAILABLE_METHODS}")',
        default=DEFAULT_AVAILABLE_METHODS,
        choices=AVAILABLE_METHODS.values()
    )
    parser.add_argument(
        "-l", "--log",
        help="Whether the decoder should log its state.",
        default=False,
        action="store_true"
    )
    parser.add_argument(
        "-k", "--kwargs",
        type=argparse.FileType("r", encoding="utf-8"),
        help="A .json file that should be read for kwargs that should be passed"
    )
    
    return parser


def parse_parser(parser: argparse.ArgumentParser) -> Kwargs:
    args = vars(parser.parse_args())
    kwargs_file = args.get("kwargs")
    
    if kwargs_file is not None:
        kwargs = json.load(kwargs_file)
    else:
        kwargs = {}
    
    video = Path(args["video"])
    
    if not video.exists():
        raise ValueError(f'Video not found! Given path: "{str(video)}"')
    
    return {
        "video": video,
        "method": args["method"],
        "log": args["log"],
        "kwargs": kwargs
    }


def handle(**arguments):
    video = arguments.pop("video")
    method = arguments.pop("method")
    log = arguments.pop("log")
    kwargs = arguments.pop("kwargs")
    
    if log is not False and (key := "log") not in kwargs:
        kwargs[key] = log
    
    data = HandleDataExtractor.decode_video(video)
    
    if method == AVAILABLE_METHODS["HANDLE"]:
        HandleDataExtractor.handle_raw_data(data, **kwargs)
    elif method == AVAILABLE_METHODS["DUMP"]:
        DumpDataExtractor.dump_to_file(data, **kwargs)
    elif method == AVAILABLE_METHODS["REVIEW"]:
        file_key = "file"
        
        if file_key not in kwargs:
            kwargs[file_key] = str(Path.cwd().joinpath("data.json"))
        if (key := "minify") not in kwargs:
            kwargs[key] = False
        
        DumpDataExtractor.dump_to_file(data, **kwargs)
        
        os.startfile(kwargs[file_key])


if __name__ == "__main__":
    logging.info("Preparing...")
    parser = create_parser()
    
    logging.info("Reading input")
    kwargs = parse_parser(parser)
    
    logging.info("Handling data")
    handle(**kwargs)
