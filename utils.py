import re
from pathlib import Path, PurePath
from typing import *

from typing_types import PathStr, SimpleBuiltinTypes


def pstr(data: PathStr) -> Path:
    if type(data) is str:
        return Path(data)
    elif isinstance(data, PurePath):
        return data
    
    try:
        raise ValueError(f'"{str(data)[:10]}"... can`t be used as path!')
    except TypeError:
        raise ValueError(f'The given value can`t be used as a path!')


def pstrnone(data) -> Optional[Path]:
    if data is None:
        return None
    return pstr(data)


def pstrcwd(data) -> Path:
    if data is None:
        return Path.cwd()
    return pstr(data)


def split_nth(data: str, split: str, n: int, keep_split: True) -> Generator[str, None, None]:
    split_data = data.split(split)
    length = len(split_data)
    suffix = split if keep_split else ""
    
    for i in range(0, length, n):
        if i + n < length:
            # Get next elements
            yield split.join(
                (split_data[i + j] for j in range(n))
            ) + suffix


def read_only_properties(*attrs):
    def class_rebuilder(cls):
        "The class decorator"
        
        class NewClass(cls):
            "This is the overwritten class"
            
            def __setattr__(self, name, value):
                if name not in attrs:
                    pass
                elif name not in self.__dict__:
                    pass
                else:
                    raise AttributeError("Can't modify {}".format(name))
                
                super().__setattr__(name, value)
        
        return NewClass
    
    return class_rebuilder


def prompt(message: str) -> bool:
    value = input("\n" + message + ' "y" for yes. ').lower()
    return value in {"y", }


int_regex = re.compile("^[+-]?\d+$")
float_regex = re.compile("^[+-]?\d*[.,]\d*$")


def string_to_type(value: str) -> SimpleBuiltinTypes:
    # None check
    if value == "None":
        return None
    
    # Boolean check
    if value == "True":
        return True
    if value == "False":
        return False
    
    # Digit check
    if re.match(int_regex, value):
        return int(value)
    if re.match(float_regex, value):
        return float(value)
    
    return value


def rename_keys(value: str) -> str:
    return value.lstrip("-").replace("-", "_")


def parse_args(args) -> Dict[str, SimpleBuiltinTypes]:
    split = [x.split("=") for x in args]
    found = {}
    
    for key, value in split:
        found[rename_keys(key)] = string_to_type(value)
    
    return found
