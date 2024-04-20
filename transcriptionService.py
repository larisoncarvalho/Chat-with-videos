import whisper
from whisper.utils import get_writer

# use whisper large-v1, this can be changed to use a bigger model if hardware allows
whisperModelName = "large-v1"

#translate uses Whisper to translate/transcribe the video to english as saves it as a .vtt file  
def translate(videoName):
    writer_options = {
            "max_line_count": 1,
            "max_words_per_line": 1
        }
    model = whisper.load_model(whisperModelName)
    result = model.transcribe("audio/"+videoName, task="translate")
    print(f' The text in video: \n {result}')
    output_directory = "./transcripts/"
    writer = get_writer("vtt", output_directory)
    writer(result, videoName[:-3]+"vtt", writer_options)

# To test the module independently
# if __name__ == "__main__":
#      translate("Terminator 1984 Full Movie in HD (Arnold Schwarzenegger);;;piPIckK_R0o.mp3")
