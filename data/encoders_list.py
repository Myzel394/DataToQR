#!/usr/bin/env python
__author__ = "Miguel Krasniqi"

from .encoders import *

FILE_ENCODERS = (
    RelativeFileEncoder,
)

ALL_ENCODERS = (
    RelativeFileEncoder,
    AbsoluteFileEncoder,
    TextEncoder,
)
