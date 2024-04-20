import yt_dlp
import os

# Download the youtube video and an mp3 file to be transcribed
def download_audio(link, videoName):
	with yt_dlp.YoutubeDL({'extract_audio':True, 'format': 'bestaudio', 'outtmpl': 'audio/'+videoName}) as video:
		info_dict = video.extract_info(link, download = True)
		video_title = info_dict['title']
		print(video_title)
		video.download(link)
		print("video downloaded")
		return video_title+".mp3"

# To test the module independently
# if __name__ == "__main__":
# 	download_audio("https://www.youtube.com/watch?v=fONodXhruyg","Intel’s Lost Their Mind;;;fONodXhruyg.mp3")
