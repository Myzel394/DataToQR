import qrcode

DELIMITER = ","
FULL_DELIMITER = ";"
BASE64_REGEX = "(?:[A-Za-z0-9+\\/]{4})*(?:[A-Za-z0-9+\\/]{2}==|[A-Za-z0-9+\\/]{3}=)?"
ENCODER_ID_REGEX = "[a-zA-Z]+"

DATA_STRING = f"{{data}}{DELIMITER}{{information}}{DELIMITER}{{encoder.encoder_id}}{FULL_DELIMITER}"
DATA_STRING_REVERSE = f"^({BASE64_REGEX}){DELIMITER}({BASE64_REGEX}){DELIMITER}({ENCODER_ID_REGEX})$"

ACTION_WRITE = "write_file"
ACTION_SHOW = "show"

DATA_CHUNK_SIZE = 2300
ENCODE_TYPE = "utf-8"

DEFAULT_OPTS = {
    "version": 1,
    "error_correction": qrcode.constants.ERROR_CORRECT_L,
    "border": 0,
    "box_size": 3
}

DEFAULT_FFMPEG_OPTS = {
    "-vcodec": "libx264",
    "-framerate": "12",
    "-preset": "slower"
}
