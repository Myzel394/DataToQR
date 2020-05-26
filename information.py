#!/usr/bin/env python
__author__ = "Miguel Krasniqi"

import base64
import json

import constants
from typing_types import JsonSerializable


def encode_information(information: JsonSerializable) -> str:
    return base64.b64encode(
        json.dumps(information, separators=(",", ":")).encode(constants.ENCODE_TYPE)
    ).decode(constants.ENCODE_TYPE)


def decode_information(information: str) -> JsonSerializable:
    return json.loads(
        base64.b64decode(
            bytes(information, constants.ENCODE_TYPE)
        )
    )
