import open_subtitles
import sys


def main():

    os = open_subtitles.OpenSubtitles()
    os.login()

    print("Downloads remaining: " + str(os.user_downloads_remaining))

    file_info = os.get_subtitle_file_info("/my/video/file.mkv", "en", True)

    os.download_subtitle(file_info['file_no'])

if __name__ == "__main__":
    main()


sys.exit(0)
