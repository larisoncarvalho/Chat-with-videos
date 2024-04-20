import ffmpeg
import os
import glob

# downloadVideoHelper downloads the video as an mp3 file for further processing 
# this helper function is for non youtube videos that use m3u8 streaming
def downloadVideoHelper(videoUrl, videoId, videoName):
    if glob.glob("audio/*;;;" +videoId+".mp3"):
        print("Video is already downloaded")
        return
    # use a temp video name while downloading to prevent videoExists check from saying video exists while its actually still downloading
    tempVideoName = "audio/temp_"+videoId+".mp3"
    ffmpeg.input(videoUrl, protocol_whitelist="file,https,tcp,tls,crypto").output(tempVideoName).run(overwrite_output=True)
    print(videoName)
    os.rename(tempVideoName, "audio/" + videoName + ";;;" +videoId+".mp3")
    print("downloaded mp3")