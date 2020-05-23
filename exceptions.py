#!/usr/bin/env python
__author__ = "Miguel Krasniqi"


class EncoderError(Exception):
    """Should be used in an encoder class for errors made my the user"""
    pass


class EncoderFailed(Exception):
    """Should be used in the actual encoding process"""
    pass


class DecoderError(Exception):
    """Should be used in an decoder class"""
    pass


class DecoderFailed(Exception):
    """Should be used in the actual decoding process"""
    pass
