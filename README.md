#What is DataToQR?
DataToQR allowes you to transform data into a video of QR-Codes, which you then can decode later.

I got the idea from a comment by "Amanda Capsicum" on this Youtube video: https://youtu.be/y2F0wjoKEhg.

#How to use this?
You can use the `qr_encoder.py` and `qr_decoder` to encode and decode data
in the console. The other files can be used as a library, you can check
docstrings for documentation and help.

The temp folder DOES NOT get automatically deleted! You have to
manually delete it or set `clear_temp=True`!

##CMD Usage
Files, folders or multiple files (separated with space) can be encoded by using 
`qr_encoder.py`. Relative and absolute paths are supported. If you want to
pass kwargs, you have to create a `.json` file with the given kwargs
in it and pass it.
###Documentation
See `qr_encoder --help` for documentation.

###Examples
####Encoding
Encode a single file:
```commandline
qr_encoder file.txt
```
---
Encode multiple files:
```commandline
qr_encoder first.txt secoond.py third.json
```
---
Encode a folder to a given output:
```commandline
qr_encoder file -o video/qr.avi
```
---
Encode a file to a given output with kwargs

kwargs.json:
```json
{
  "information_opts": {
    "relative_to": "C:\\Users\\<youruser>\\PycharmProjects\\DataToQR"
  }
}
```
Input:
```commandline
qr_encoder file.txt -o video/qr.avi -k kwargs.json
```
####Decoding
Decode a video:
```commandline
qr_decoder qr_data.avi
```
---
Dump the value of the decoded video;
```commandline
qr_decoder qr_data.avi -m dump
```
---
Dump the value of the decoded video and show it:
```commandline
qr_decoder qr_data.avi -m review
```
---
Decode a video with kwargs

kwargs.json:
```json
{
  "base_path": "C:\\Users\\<youruser>\\PycharmProjects\\DataToQR"
}
```
Input:
```commandline
qr_decoder qr_data.avi -k kwargs.json
```
---
##Python Usage
###Documentation
There are documentation strings for most of the classes, methods and
functions. A generic documentation will be added later.

In a nutshell:

| Value        	| Explanation                                        	|
|--------------	|----------------------------------------------------	|
| get_data.... 	| Returns data based on your input                   	|
| encode...    	| Encodes data (creates a video) based on given data 	|
| decode...    	| Just decodes and does not handle                   	|
| handle...    	| Handles the given decoded data                     	|

###Examples
```python
from encode import FileDataInsertor

if __name__ == "__main__":  # <-- IMPORTANT !!!
    # Encode a single file
    FileDataInsertor.encode_file("test.txt")

    # Encode all ".txt" files in a folder
    FileDataInsertor.encode_folder("folder", "output.avi", folder_glob="*.txt")
    
    # Encode a string
    data = FileDataInsertor.get_encoded_data("My String")
    FileDataInsertor.create_video(data)
```

#How does this work?
##Encoding
The encoding works in four steps:
1. Collect data
3. Split data & create QR-Code images
4. Create a video from the images
###Collect data
Data collection works in two steps:
1. Collect actual data
2. Collect information about the data

The information is a JSON string. The actual data and the information about 
the JSON information will both be converted to base64-format. The information
contains only the necessary information to handle the actual data.
E.g. if you have a file, the file name and encoding will be saved in the
information part.

The final data will also contain information about what encoder was used.
These parts will be separated using a separator.

The collected data follows this scheme:
```
<actual data in base64><delimiter><JSON information in base64><delimiter><encoder id><package_delimiter>
```
###Split data & create QR-Code images
The data will be split into smaller parts so a QR-Code can be generated.
The QR-Code images will be saved in a temporary folder.
###Create a video from the images
The QR-Code images will be put to a video using `ffmpeg`.
##Decoding
The decoding process simply reads the QR-Codes from the video and handles 
them using the associated decoder.