#!/usr/bin/env python
__author__ = "Miguel Krasniqi"

from .encoders import *

FILE_ENCODERS = (
    FileEncoder,
    BytesEncoder
)

ALL_ENCODERS = (
    FileEncoder,
    BytesEncoder,
    TextEncoder,
)
