import db_adder
import subprocess
from pathlib import Path
import os


def download(basepath, vod_id):
    drive_path = basepath+str(vod_id)

    # First, download twitch chat logs using twitch-chat-downloader: https://github.com/PetterKraabol/Twitch-Chat-Downloader
    # This will create a folder named by the vod ID, and two subfolders for the source files and output files

    # Path(drive_path+'/source/').mkdir(parents=True, exist_ok=True)
    # Path(drive_path+'/output/').mkdir(parents=True, exist_ok=True)

    # If the chat log already exists, no need to re-download it.
    # if not os.path.isfile(drive_path+'/source/'+str(vod_id)+'.log'):
    #     print(drive_path+'/source/'+str(vod_id)+'.log')
    #     print('No chatlogs found for this stream id found... downloading chat logs...')
    subprocess.run(["tcd", '--channel', 'MOONMOON', 'last=1', '--format', 'irc', '--output', 'G:/MOONMOON/highlights/source/'])
    #     exit()
    #     db_adder.main(vod_id)
    # else:
    #     print("Using downloaded chat logs for ", vod_id)



    # Download the vod id as an mp3 file using twitch-dl: https://github.com/ihabunek/twitch-dl
    # This code allows for the downloading of the vod in multiple parts. If using this functionality, the .mp3 filenames
    #   MUST end with ' [#].mp3', where [#] is the part of the vod, ie 1, 2, 3 etc.
    #       Don't forget the 'space' before the number, or the program will fail.

    # It is recommended that the bitrate of the mp3 files be reduced to save time/storage. 96kbps seems to work fine.
    # TODO: implement auto-download of mp3 files  -  [done, needs testing]

    # if len(glob.glob1(drive_path+'/source/', '*mp3')+glob.glob1(drive_path+'/source/', '*mkv')) == 0:
    #     print('No audio files found for this stream id... downloading vod audio...')
    #     subprocess.run(['twitch-dl', 'download', str(vod_id), '-q', 'audio_only', '--output', drive_path+'/source/{id}.mkv'], shell=True)
    #     subprocess.run(["./ffmpeg", "-i", drive_path+'/source'+str(vod_id)+'.mkv', drive_path+'/source/'+str(vod_id)+'.mp3', "-vn", "-acodec", "copy"])
    # else:
    #     print('Using downloaded vod file for ', vod_id)
    # # Next, create a transcipt of the stream. This is done using videogrep: https://github.com/antiboredom/videogrep
    #
    # dirname = drive_path + '/source/'
    # directory = os.fsencode(dirname)
    # # num_mp3 = len(glob.glob1(dirname, '*mp3'))  # Number of mp3 files in the source directory. Each mp3 needs a separate transcript file created
    # for file in os.listdir(directory):
    #     filename = os.fsdecode(file)
    #     # Only create the transcript if the json file doesn't exist already for the given mp3 file.
    #     if filename.endswith(tuple([".mp3", '.mkv'])) and not os.path.isfile(dirname+filename.replace('mkv', 'json')):
    #         print('No transcription files found for {{m:.2s}} ... generation transcript...'.format(m=filename))
    #         fpath = dirname+filename
    #         subprocess.run(['videogrep', '-i', fpath, '--transcribe', '--model', 'D:\IdeaProjects\PyCharm\yt-transcribe\model-large'], shell=True)
    # print('Transcription complete for ', vod_id)
    # # Combine the .json transcription files into a single .csv file
    # # Only do this if a chatlog does not exist
    # if not os.path.isfile(drive_path+'/output/chatlog.csv'):
    #     print('Generating csv transcript from json files...')
    #     transcribe.make_transcript(drive_path)


# Now we have finished the collection and pre-processing of the data.
