#!/usr/bin/env python
__author__ = "Miguel Krasniqi"

from typing import *

JsonSerializable = Dict[str, Union[None, str, int, float, bool, list, dict]]

#                       Data, Information, Encoder
PackedDataTuple = Tuple[str, JsonSerializable, Type["BaseDataEncoderInterface"]]
