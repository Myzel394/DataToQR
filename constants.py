DELIMITER = ";"
BASE64_REGEX = "(?:[A-Za-z0-9+/]{4})*(?:[A-Za-z0-9+/]{2}==|[A-Za-z0-9+/]{3}=)"
ENCODER_ID_REGEX = "[a-zA-Z]+"

DATA_STRING = f"{{data}}{DELIMITER}{{information}}{DELIMITER}{{encoder.encoder_id}}{DELIMITER}"
DATA_STRING_REVERSE = f"({BASE64_REGEX}){DELIMITER}({BASE64_REGEX}){DELIMITER}({ENCODER_ID_REGEX}){DELIMITER}"

ACTION_WRITE = "write_file"
ACTION_SHOW = "show"

DATA_CHUNK_SIZE = 1500
ENCODE_TYPE = "utf-8"
