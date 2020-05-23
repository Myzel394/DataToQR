from pathlib import Path, PurePath
from typing import *

from data.typing_types import PathStr


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
    value = input(message + ' "y" for yes. ').lower()
    return value in {"y", }
