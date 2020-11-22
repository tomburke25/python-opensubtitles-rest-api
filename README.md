# python-opensubtitles-rest-api
Module to get a subtitle from OpenSubtitles

Uses the new REST API at https://opensubtitles.stoplight.io/

Requires an account at OpenSubtitles.com 

You will need to create an API key in your account

**API is currently in BETA**

## Basic Usage:

Create a credentials file called .credentials:

    { 'username' : 'YOURUSER' , 'password': 'YOURPASS', 'api-key': 'YOURAPIKEY' }


```python
import open_subtitles
os = open_subtitles.OpenSubtitles()
os.login()
file_info = os.get_subtitle_file_info("/my/video/file.mkv", "en", True)
os.download_subtitle(file_info['file_no'])
```


Search for a subtitle:
```python
get_subtitle_file_info(full_file_path, sublanguage, forced)
```
* full_file_path = *required*
* sublanguage = *required*
* forced = *optional* (default=False)

Download subtitle:
```python
download_subtitle(file_no, output_directory, output_filename, overwrite)
```
* file_no = *required*
* output_directory = *optional* (default=same as video file)
* output_filename = *optional* (default=same as video file)
* overwrite = *optional* (default=False)
    
FileOperations module contains code for the hashing from the XML-RPC implementation by Alexandre González at:
https://raw.githubusercontent.com/agonzalezro/python-opensubtitles