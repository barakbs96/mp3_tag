from acrcloud.recognizer import ACRCloudRecognizer
import os
import mp3_tagger
from shutil import copyfile
import logging
import json
import traceback
from my_config import HOST, ACCESS_KEY, ACCESS_SECRET

LOG_FORMAT = '%(asctime)s:%(levelname)s:%(message)s'
SONGS_PATH = r"c:\temp\songs"
SONGS_TEMP_NAME = r"tempi.mp3"
PARENT_DIR = os.path.dirname(SONGS_PATH)
NEW_SONGS_DIR_NAME = r"edited_songs"
MP3_EXTENSION = r"mp3"
SUCCESS_MSG = 'Success'

config = {
    'host': HOST,
    'access_key': ACCESS_KEY,
    'access_secret': ACCESS_SECRET,
    'debug': True,
    'timeout': 10
}
 
def list_files(directory, extension):
    return (f for f in os.listdir(directory) if f.endswith('.' + extension))

def create_new_songs_folder(songs_path, new_dir):
    if not os.path.exists(os.path.join(PARENT_DIR,new_dir)):
        os.makedirs(os.path.join(PARENT_DIR,new_dir))
    return os.path.join(PARENT_DIR,new_dir)
    
def init_logger():
    logFormatter = logging.Formatter(LOG_FORMAT)
    rootLogger = logging.getLogger()

    fileHandler = logging.FileHandler(os.path.join(PARENT_DIR,NEW_SONGS_DIR_NAME,'log.log'))
    fileHandler.setFormatter(logFormatter)
    rootLogger.addHandler(fileHandler)

    consoleHandler = logging.StreamHandler()
    consoleHandler.setFormatter(logFormatter)
    rootLogger.addHandler(consoleHandler)
    rootLogger.setLevel(logging.DEBUG)
    return rootLogger

def get_song_artists(info):
    artists = ''
    for artist in info['metadata']['music'][0]['artists']:
        artists += artist['name']+"/"
    return artists[:-1]

def get_song_album(info):
    return info['metadata']['music'][0]['album']['name']

def get_song_title(info):
    return info['metadata']['music'][0]['title']

def copy_to_temp(src, dst):
    new_path = os.path.join(dst,SONGS_TEMP_NAME)
    copyfile(src,new_path)
    return new_path
    
if __name__ == "__main__":
    edited_path = create_new_songs_folder(SONGS_PATH,NEW_SONGS_DIR_NAME)
    l = init_logger()
    l.info("logger initialized")
    l.info("edited songs folder created")
    songs_list = list_files(SONGS_PATH,MP3_EXTENSION)
    acrcloud = ACRCloudRecognizer(config)
    l.info("acrcloud recognizer configured")    
    for song_name in songs_list:
        try:
            l.info("editing song {0}".format(song_name))
            temp_path = copy_to_temp(os.path.join(SONGS_PATH,song_name),edited_path)
            info = json.loads(acrcloud.recognize_by_file(temp_path, start_seconds=0))
            if info['status']['msg'] != 'Success':
                l.warning("Did not recognize song: {0}. Status: {1}".format(song_name,info['status']['msg']))
                continue
            l.info('song recognized successfully')
            new_song_path = os.path.join(edited_path,get_song_title(info)+"."+MP3_EXTENSION) 
            copyfile(temp_path, new_song_path)
            l.info('song copied to edited folder, path:{0}'.format(new_song_path))
            mp3_file = mp3_tagger.MP3File(new_song_path)
            mp3_file.album = get_song_album(info)
            mp3_file.artist = get_song_artists(info)
            mp3_file.song = get_song_title(info)    
            l.info("Edited values: album: {0}, artists: {1}, song: {2}".format(mp3_file.album, mp3_file.artist, mp3_file.song))
            mp3_file.save()
        except Exception as e:
            l.error('Error: {0} song:{1}',e, song_name)
            l.error('Trace: {0}',traceback.format_exc())
            
    