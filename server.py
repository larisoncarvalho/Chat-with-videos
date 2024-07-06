import indexerService
from flask import Flask,request,stream_with_context, Response, send_file, jsonify
import json
import glob
import llmService
from flask_executor import Executor
from flask_cors import CORS
from llama_index.core.storage.chat_store import SimpleChatStore
from llama_index.core.memory import ChatMemoryBuffer
import asyncio
import os
import re

app = Flask(__name__)
CORS(app)
executor = Executor(app)
index = None

# transcribeVideo calls the transcription service to download, transcribe and index the video in the background
@app.route('/transcribeVideo', methods=['POST'])
def download_video():
    requestData = json.loads(request.data)

    # call videoExists to check if video is already indexed or is in progress, if so then return 409 (conflict)
    videoExistsCheck = videoExists(videoId=requestData["videoId"])
    if videoExistsCheck.status_code == 200 or videoExistsCheck.status_code == 202:
        return jsonify({"status":"rejected"}), 409
    
    # Call transcribeVideo on a background thread
    executor.submit(indexerService.processYoutubeVideo,requestData["url"], requestData["videoName"], requestData["videoId"])
    data = {"status":"accepted"}
    return jsonify(data), 201

# subtitles endpoint is used in cases where the video already has a subtitles file on Youtube and we want to use that instead of transcribing the video ourselves
@app.route('/uploadSubtitles', methods=['POST'])
def download_subtitles():
    response = Response(status=201)
    f = request.files['file'] 
    f.save(f.filename)
    return response

#videoExists checks if the video is indexed, inprogress, or not indexed
# 200 -> Indexed and available
# 202 -> transcription and indexing is in progress
# 404 -> Not indexed
@app.route('/videoExists/<videoId>', methods=['GET'])
def videoExists(videoId):
    if glob.glob("llamaindex/"+videoId+"_summary"):
        return Response(status=200)
    elif glob.glob("transcripts/*;;;"+videoId+".vtt") or glob.glob("audio/*"+videoId+".wav"):
        return Response(status=202)
    else:
        return Response(status=404)

# downloadSubtitles endpoint is used to download the transcribed video as a VTT subtitles file
@app.route('/downloadSubtitles/<videoId>', methods=['GET'])
def downloadFile (videoId):
    file_path = glob.glob("transcripts/*;;;"+videoId+".vtt")
    if file_path:
        return send_file(file_path[0], as_attachment=True)

    return Response(status=404)

#chat is the endpoint used to interact with a the LLM in a Q and A style using the provided videoId as the context
@app.route('/chat', methods=['POST'])
def chat():
    requestData = json.loads(request.data)

    if requestData['videoId'] == None or requestData['prompt'] == None:
        return Response(status=400)
    
    chatMemory = None
    chatStore = SimpleChatStore()
    
    if "userId" in requestData and requestData['userId'] != None:       
        if os.path.exists("./llamaindex/chat_store.json"):
            chatStore = SimpleChatStore.from_persist_path(
                    persist_path="./llamaindex/chat_store.json"
                )
        chatMemory = ChatMemoryBuffer.from_defaults(
            token_limit=3000,
            chat_store=chatStore,
            chat_store_key=requestData['userId'],
        )
    chat_engine = llmService.getChatEngine(requestData['videoId'], chatMemory)
    if chat_engine == None:
        return Response(status=404)
    else:
        # chat_engine.reset()
        prompt = requestData['prompt']
        # Create a new event loop
        loop = asyncio.new_event_loop()

        # Set the event loop as the current event loop
        asyncio.set_event_loop(loop)
        #response = chat_engine.stream_chat(prompt)
        response = chat_engine.chat(prompt)
        chat_engine.reset()
        # pattern = re.compile(r'\(\s*(?:\d+% )?(\d{2}:\d{2}(?:\.\d{3})? - \d{2}:\d{2}(?:\.\d{3})?)\s*(?:\d+% )?(?:\s*\d*%?\s*)?\)?')
        pattern = re.compile(r'\((.*?(\d{2}:\d{2}:\d{2}(?:\.\d{3})? - \d{2}:\d{2}:\d{2}(?:\.\d{3})?).*?)\)')
        responseText = response.response.replace("\n","<br>")
        responseText = re.sub(pattern, r'<a>\2</a>', responseText)
        if "userId" in requestData and requestData['userId'] != None:
            chatStore.persist(persist_path="./llamaindex/chat_store.json")
        data = {
             "response": responseText.replace("<a>","<br><a>")
        }
        return jsonify(data)
        #return stream_with_context(response.response_gen)

# summary endpoint returns a summary of the video
@app.route('/summary/<videoId>', methods=['GET'])
def summary(videoId):
    if videoId == None:
        return Response(status=400)
    summary_response = llmService.getSummary(videoId)
    if summary_response == None:
        return Response(status=404)
    # pattern = re.compile(r'\(\s*(?:\d+% )?(\d{2}:\d{2}(?:\.\d{3})? - \d{2}:\d{2}(?:\.\d{3})?)\s*(?:\d+% )?(?:\s*\d*%?\s*)?\)?')
    pattern = re.compile(r'\((.*?(\d{2}:\d{2}:\d{2}(?:\.\d{3})? - \d{2}:\d{2}:\d{2}(?:\.\d{3})?).*?)\)')
    responseText = summary_response.replace("\n","<br>")
    responseText = re.sub(pattern, r'<a>\2</a>', responseText)
    data = {
    "response": responseText
      }
    return jsonify(data)

#chat is the endpoint used to interact with a the LLM in a Q and A style using the provided videoId as the context
@app.route('/globalChat', methods=['POST'])
def globalChat():
    requestData = json.loads(request.data)
    
    chatMemory = None
    chatStore = SimpleChatStore()
    
    if "userId" in requestData and requestData['userId'] != None:       
        if os.path.exists("./llamaindex/chat_store.json"):
            chatStore = SimpleChatStore.from_persist_path(
                    persist_path="./llamaindex/chat_store.json"
                )
        chatMemory = ChatMemoryBuffer.from_defaults(
            token_limit=3000,
            chat_store=chatStore,
            chat_store_key=requestData['userId']+"_global",
        )
    
    if requestData['prompt'] == None:
        return Response(status=400)
    chat_engine = llmService.getChatEngine("global", chatMemory)
    if chat_engine == None:
        return Response(status=404)
    else:
        prompt = requestData['prompt']
        # Create a new event loop
        loop = asyncio.new_event_loop()

        # Set the event loop as the current event loop
        asyncio.set_event_loop(loop)
        #response = chat_engine.stream_chat(prompt)
        response = chat_engine.chat(prompt)
        sourcesResponse = ""
        for source in response.source_nodes:
            fileData = source.metadata["file_name"].split(";;;")
            sourcesResponse+="<a target=\"_blank\" href=\"https://www.youtube.com/watch?v="+fileData[1][:-4]+"\">"+fileData[0]+"</a><br>"
        chat_engine.reset()
        if "userId" in requestData and requestData['userId'] != None:
            chatStore.persist(persist_path="./llamaindex/chat_store.json")
            
        data = {
            "response": response.response.replace("\n","<br>").replace("(2%","<a>").replace("2%)","</a><br>")+"<br><br>Sources:<br>"+sourcesResponse,
            }
        return jsonify(data)
        #return stream_with_context(response.response_gen)


if __name__ == "__main__":
    app.run(host='0.0.0.0', port=2020)
