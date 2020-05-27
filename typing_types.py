#!/usr/bin/env python
__author__ = "Miguel Krasniqi"

from pathlib import Path
from typing import *

JsonSerializable = Dict[str, Union[None, str, int, float, bool, list, dict]]

#                       Data, Information, Encoder
PackedDataTuple = Tuple[str, JsonSerializable, Type["BaseDataEncoderInterface"]]
PackedDataTupleNotResolved = Tuple[str, JsonSerializable, str]
PathStr = Union[Path, str]
Kwargs = Dict[str, Any]
SimpleBuiltinTypes = Union[bool, int, float, str, None]
DataList = List[List[str]]
