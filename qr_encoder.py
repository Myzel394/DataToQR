#!/usr/bin/env python
__author__ = "Miguel Krasniqi"

import argparse
import json
import logging

from encode import FileDataInsertor
from typing_types import *
from typing_types import Kwargs


def create_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Encode data into a video of QR-Codes.")
    parser.add_argument(
        "target",
        type=str,
        help=f'A single file, a folder or multiple files. You can use an absolute path or a relative one, '
             f'which is relative to "{Path.cwd().absolute()}".',
        nargs="+",
    )
    parser.add_argument(
        "-o", "--output",
        type=str,
        help="The output video file path",
        default=None
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
    
    output = args.get("output")
    
    target: List[str] = args["target"]
    found: Set[Path] = set()
    for element in target:
        if (path := Path(element)).exists():
            found.add(path)
        else:
            logging.warning(f'Path "{element}" will be skipped because it doesn`t exist.')
    
    return {
        "target": found,
        "output": output,
        "kwargs": kwargs
    }


def handle(**arguments):
    target = arguments.pop("target")
    output = arguments.pop("output")
    kwargs = arguments.pop("kwargs")
    
    FileDataInsertor.encode_multiple(target, output, **kwargs)


if __name__ == "__main__":
    logging.info("Preparing...")
    parser = create_parser()
    
    logging.info("Reading input")
    kwargs = parse_parser(parser)
    
    logging.info("Handling data")
    handle(**kwargs)
