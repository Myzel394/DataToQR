DELIMETER = ";"
BASE64_REGEX = "(?:[A-Za-z0-9+/]{4})*(?:[A-Za-z0-9+/]{2}==|[A-Za-z0-9+/]{3}=)"
ENCODER_ID_REGEX = "[a-zA-Z]+"

DATA_STRING = f"{{data}}{DELIMETER}{{information}}{DELIMETER}{{encoder.encoder_id}}"
DATA_STRING_REVERSE = f"({BASE64_REGEX}){DELIMETER}({BASE64_REGEX}){DELIMETER}({ENCODER_ID_REGEX})"

ACTION_WRITE = "write_file"
ACTION_SHOW = "show"

DATA_CHUNK_SIZE = 2500
ENCODE_TYPE = "UTF-8"
