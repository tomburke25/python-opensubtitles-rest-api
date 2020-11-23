from FileOperations import File
from urllib.parse import urlencode

import os
import requests
import requests_cache
import json
import sys


class OpenSubtitles(object):

    def __init__(self):

        # reduce load on API server with local cache
        # I haven't run any tests to see how effective this is
        requests_cache.install_cache(cache_name='opensubtitle_cache', backend='sqlite', expire_after=600)

        # stop cache growing too big
        requests_cache.remove_expired_responses()

        self.login_token = ""
        self.user_downloads_remaining = ""
        self.folder_path = ""
        self.file_name = ""
        self.sublanguage = ""
        self.forced = ""

        # import secrets from .credentials file. Or remove this and hard code them.
        try:
            self.credentials_dic = []
            with open('.credentials', 'r') as credential_file:
                self.credentials_dic = eval(credential_file.read())
                self.username = self.credentials_dic['username']
                self.password = self.credentials_dic['password']
                self.apikey = self.credentials_dic['api-key']

        except FileNotFoundError:
            print("No credentials file found at \"" + os.path.dirname(os.path.realpath(__file__)) + "/.credentials\"")
        except KeyError:
            print("Incorrectly formatted secrets in .credentials file")

    # make login request. Returns auth token
    def login(self):

        # build login request
        login_url = "https://www.opensubtitles.com/api/v1/login"
        login_headers = {'api-key': self.apikey, 'content-type': 'application/json'}
        login_body = {'username': self.username, 'password': self.password}

        try:
            login_response = requests.post(login_url, data=json.dumps(login_body), headers=login_headers)
            login_response.raise_for_status()
            login_json_response = login_response.json()

            # this is our login token, we need it later
            self.login_token = login_json_response['token']
        except requests.exceptions.HTTPError as httperr:
            raise SystemExit(httperr) # need more documentation to know exactly what the API HTTP error responses are
        except requests.exceptions.RequestException as reqerr:
            raise SystemExit("Failed to login: " + reqerr)
        except ValueError as e:
            raise SystemExit("Failed to parse login JSON response: " + e)

        # build user request
        user_url = "https://www.opensubtitles.com/api/v1/infos/user"
        user_headers = {'api-key': self.apikey, 'authorization': self.login_token}

        try:
            # dont cache remaining_downloads, as this changes every time
            with requests_cache.disabled():
                user_response = requests.get(user_url, headers=user_headers)
                user_response.raise_for_status()

                # standard accounts have a low limit. Upgrade to VIP if you want more. It's about 10EUR a year.
                user_json_response = user_response.json()
                self.user_downloads_remaining = user_json_response['data']['remaining_downloads']

        except requests.exceptions.HTTPError as httperr:
            raise SystemExit(
                httperr)  # need more documentation to know exactly what the API HTTP error responses are
        except requests.exceptions.RequestException as reqerr:
            raise SystemExit("Failed to login: " + reqerr)
        except ValueError as e:
            raise SystemExit("Failed to parse user JSON response: " + e)

    # get the first hash matching subtitle file
    def get_subtitle_file_info(self, full_file_path, sublanguage, forced=False):

        # file to inspect
        self.folder_path = str(os.path.dirname(full_file_path))
        self.file_name = str(os.path.basename(full_file_path))
        self.sublanguage = sublanguage
        self.forced = forced

        try:
            file_to_inspect = File(full_file_path)
        except FileNotFoundError as fileerr:
            SystemExit("Input video file could not be found")

        # add additional query params here. May be able to sort by rating etc once API is updated.
        try:
            query_params = {'moviehash': file_to_inspect.get_hash(),
                            'foreign_parts_only': 'only' if forced else 'exclude',
                            'languages': self.sublanguage,
                            'query': self.file_name}

            # uncomment if you are having problems with filename special character encoding problems
            #query_params = urlencode(query_params)

            # build query request
            query_url = 'https://www.opensubtitles.com/api/v1/subtitles?'
            query_headers = {'api-key': self.apikey}
            query_response = requests.get(query_url, params=query_params, headers=query_headers)
            query_response.raise_for_status()
            query_json_response = query_response.json()

            # get file number from first item, first file
            query_file_no = query_json_response['data'][0]['attributes']['files'][0]['file_id']
            query_file_name = query_json_response['data'][0]['attributes']['files'][0]['file_name']

        except requests.exceptions.HTTPError as httperr:
            raise SystemExit(httperr)  # need more documentation to know exactly what the API HTTP error responses are
        except requests.exceptions.RequestException as reqerr:
            raise SystemExit("Failed to login: " + reqerr)
        except ValueError as e:
            raise SystemExit("Failed to parse search_subtitle JSON response: " + e)

        return {'file_no': query_file_no, 'file_name': query_file_name}

    # download a single subtitle file using the file_no
    def download_subtitle(self, file_no, output_directory=None, output_filename=None, overwrite=False):

        # default saves to same folder as video file
        # cant set instance variable as a default argument, so a bit messy. Also it's late. I'm tired.
        download_directory = self.folder_path if output_directory is None else output_directory

        download_filename = os.path.splitext(self.file_name)[0] if output_filename is None else output_filename
        download_filename += "." + self.sublanguage
        download_filename += ".forced" if self.forced else ""
        download_filename += ".srt"

        # build download request
        download_url = "https://www.opensubtitles.com/api/v1/download"
        download_headers = {'api-key': self.apikey,
                            'authorization': self.login_token,
                            'content-type': 'application/json'}
        download_body = {'file_id': file_no}

        # dont download if subtitle already exists
        if os.path.exists(download_directory + os.path.sep + download_filename) and not overwrite:
            print("Subtitle file " + download_directory + os.path.sep + download_filename + " already exists")
            sys.exit(0)

        # only download if user has download credits remaining
        if self.user_downloads_remaining > 0:

            try:
                # this will cost a download
                download_response = requests.post(download_url, data=json.dumps(download_body), headers=download_headers)
                download_json_response = download_response.json()

                # get the link stored on the server
                download_link = download_json_response['link']

                # download the file
                download_remote_file = requests.get(download_link)
                open(download_directory + os.path.sep + download_filename, 'wb').write(download_remote_file.content)

            except requests.exceptions.HTTPError as httperr:
                raise SystemExit(httperr)  # need more documentation to know exactly what the API HTTP error responses are
            except requests.exceptions.RequestException as reqerr:
                raise SystemExit("Failed to login: " + reqerr)
            except ValueError as e:
                raise SystemExit("Failed to parse search_subtitle JSON response: " + e)
        else:
            print("Download limit reached. Please upgrade your account or wait for your quota to reset (~24hrs)")
            sys.exit(0)