#!/usr/bin/env python
__author__ = "Miguel Krasniqi"

import base64
import json
from typing import *

import constants


def is_base64(s: str) -> bool:
    try:
        return base64.b64encode(base64.b64decode(bytes(s, constants.ENCODE_TYPE))).decode(constants.ENCODE_TYPE) == s
    except:
        return False


def is_json_serializable(s: Any) -> bool:
    try:
        json.dumps(s)
        return True
    except:
        return False
