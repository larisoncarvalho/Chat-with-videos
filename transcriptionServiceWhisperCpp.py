import subprocess

# ./main -m /Users/larisoncarvalho/Documents/whisper.cpp/models/ggml-large-v3-q5_0.bin ../Chat-with-videos/audio/output.wav

# use whisper large-v1, this can be changed to use a bigger model if hardware allows
modelPath = "whisper.cpp/models/ggml-large-v3.bin"

#translate uses Whisper to translate/transcribe the video to english as saves it as a .vtt file  
def translate(videoName):

    command = ["./whisper.cpp/main", "-m", modelPath, "-f", "audio/"+videoName,
               "-bs", "5", "-et", "2.8", "-mc", "64",
                "-tr", "-ovtt", "-of", "transcripts/"+videoName[:-4]]
    subprocess.call(command)

    

# To test the module independently
# if __name__ == "__main__":
#      translate("Intel’s Lost Their Mind;;;fONodXhruyg.wav")
