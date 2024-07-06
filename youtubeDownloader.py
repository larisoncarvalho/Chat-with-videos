import yt_dlp
import os
import subprocess

# Download the youtube video and an mp3 file to be transcribed
def download_audio(link, videoName):
	with yt_dlp.YoutubeDL({'extract_audio':True, 'format': 'bestaudio', 'outtmpl': 'audio/'+videoName}) as video:
		info_dict = video.extract_info(link, download = True)
		video_title = info_dict['title']
		print(video_title)
		video.download(link)
		command = ["ffmpeg", "-i", "audio/"+videoName, "-acodec", "pcm_s16le", "-ac", "1", "-ar", "16000", "audio/"+videoName[:-4]+".wav"]
		subprocess.call(command)
		command = ["rm", "audio/"+videoName]
		subprocess.call(command)
		return video_title+".wav"

# To test the module independently
# if __name__ == "__main__":
# 	download_audio("https://www.youtube.com/watch?v=fONodXhruyg","Intel’s Lost Their Mind;;;fONodXhruyg.mp3")
