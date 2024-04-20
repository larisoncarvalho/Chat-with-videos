import helpers
from pathvalidate import sanitize_filename
import transcriptionService
import llmService
import youtubeDownloader
import re

def processYoutubeVideo(videoUrl, videoName, videoId):
	sanitizedFileName = sanitize_filename(videoName)
	sanitizedFileName = re.sub(r'[^\x00-\x7F]+', '', sanitizedFileName)
	videoName = sanitizedFileName + ";;;"+videoId+".mp3"
	youtubeDownloader.download_audio(videoUrl, videoName)
	transcriptionService.translate(videoName= videoName)
	llmService.generateIndex(videoName=videoName)
	return

# To test the module independently
# if __name__ == "__main__":
#        processYoutubeVideo("https://www.youtube.com/watch?v=s5C1LxTIpT8&ab_channel=TechLinked","Major Windows 11 Feature, GONE", "s5C1LxTIpT8")
