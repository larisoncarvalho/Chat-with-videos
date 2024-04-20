from llama_index.readers.file import UnstructuredReader
from pathlib import Path
from llama_index.core import  SimpleDirectoryReader, VectorStoreIndex, StorageContext, get_response_synthesizer, DocumentSummaryIndex, load_indices_from_storage, load_index_from_storage
from llama_index.llms.ollama import Ollama
from llama_index.core.node_parser import SentenceSplitter
import os
from llama_index.core import Settings

# pip uninstall python-libmagic
# pip uninstall python-magic 

# # install the working one
# pip install python-magic-bin
# pip install llama-index-embeddings-huggingface
mistral = Ollama(temperature=0, model="mistral", request_timeout=999999.0)

#generateIndex generates an indiviual index and a summary index for the video as well as adds the video to a global index.
def generateIndex(videoName):
    loader = UnstructuredReader()
    doc = loader.load_data(
        file=Path("./transcripts/"+videoName[:-3]+"vtt"), split_documents=False
    )
    doc[0].metadata = {"video name": videoName.split(";;;")[0], "video Id":videoName.split(";;;")[1][:-4]}
    doc[0].doc_id = videoName.split(";;;")[1][:-4]
    Settings.llm = mistral
    Settings.embed_model = "local"
    storage_context = StorageContext.from_defaults()
    cur_index = VectorStoreIndex.from_documents(
        doc,
        storage_context=storage_context,
    )
    cur_index.storage_context.persist(persist_dir="./llamaindex/"+videoName.split(";;;")[1][:-4])

    # Generate global index for the global search function
    if not os.path.exists("./llamaindex/global"):
        transcripts = SimpleDirectoryReader("./transcripts").load_data()
        global_index = VectorStoreIndex.from_documents(
        transcripts,
        storage_context=storage_context,
        )
        global_index.set_index_id("global_vector_index")
        global_index.storage_context.persist(persist_dir="./llamaindex/global")
    else:
        # # load index
        global_index = load_index_from_storage(StorageContext.from_defaults(persist_dir="./llamaindex/global"), index_id="global_vector_index")
        transcripts = SimpleDirectoryReader("./transcripts").load_data()
        global_index.refresh_ref_docs(transcripts)
        global_index.storage_context.persist(persist_dir="./llamaindex/global")

    # Pre generated summary that will be used to quickly return the summary of the video
    print("Generating summary index")
    summary_prompt = (
        "You are provided a video transcript file with timestamps as the input."
        "Refer to the document as the video and avoid calling it a transcript."
        "Your job is to summarise the video in such a way that the user reading your summary can clearly understand what was discussed in the video without having to watch the entire video."
        "This summary section should NOT contain any timestamps."
        "The goal of these key moments is that the user can watch only the moments in the video that are important and skip all the fluff and banter so create these key moments accordingly."
        "Create a section at the end of your response called 'Highlight Reels' that are clips of around 10 to 40 seconds containing the most noteworth segments from the entire video."
        "Always mention the corresponding timestamp from the video document for each of the highlight reels. The format should always be as follows: (2% <start timestamp> - <end timestamp> 2%)."
        "Such that the string '2%' denotes the start and end of the timestamp range with a single space between 2% and the time value. For example: (2% 00:10:00 - 00:13:15 2%). You must always strictly follow this format and not any other variation of it."
        "Only the highlight reel section will contain timestamps and the timestamps should strictly follow the format (2% <start timestamp> - <end timestamp> 2%) followed by the highlighted text."
    )
    
    splitter = SentenceSplitter(chunk_size=1024)
    response_synthesizer = get_response_synthesizer(
    response_mode="tree_summarize", use_async=True, llm = mistral,
    )
    doc_summary_index = DocumentSummaryIndex.from_documents(
    doc,
    llm=mistral,
    transformations=[splitter],
    response_synthesizer=response_synthesizer,
    show_progress=True,
    summary_query = summary_prompt
    )
    doc_summary_index._storage_context.persist(persist_dir="./llamaindex/"+videoName.split(";;;")[1][:-4]+"_summary")
    print(doc_summary_index.get_document_summary(videoName.split(";;;")[1][:-4]))

#getChatEngine returns the chatEngine with the transcript corresponding to the videoID in its context    
def getChatEngine(videoId, chatMemory):
    Settings.llm = mistral
    Settings.embed_model = "local"
    
    if videoId != "global":
        if not os.path.exists("./llamaindex/"+videoId):
            return None
        else:
            index = load_index_from_storage(
                StorageContext.from_defaults(persist_dir="./llamaindex/"+videoId),
            )    
        chat_engine = index.as_chat_engine(chat_mode="condense_plus_context", verbose=True, llm=mistral, memory = chatMemory,
                                        context_prompt=(
            "You are a video chatbot. You operate with the video transcript that is provided to you."
            "Your goal is to provide answers to the users and answer their questions."
            "If something is not provided in the video transcript, do not try to guess an answer. Say that there is no information on it."
            "Assume that all the questions are in the context of this video transcript. Do not provide answers for generic queries that are not related to the video in context."
            "Here is the relevant transcript for the video:\n"
            "{context_str}"
            "\nInstructions: Based on the above document, provide a detailed answer for the user question below."
            "Always Refer to the document as the video and avoid calling it a transcript."
            "Always Make each point of your response a new paragraph so that it is easy to read"
            "It is of paramout importance that your answers are of the highest accuracy and completeness in line with the video context that is provided."
            "Always mention the corresponding timestamp from the video document to support your answers. The format should always strictly be as follows: (2% <start timestamp> - <end timestamp> 2%)."
            "The timestamp in your response must be in the same format as in the transcript provided to you, hh:mm:ss.ms."
            "Such that the string '2%' denotes the start and end of the timestamp string and there is a single space between 2% and the time value. For example: (2% 00:10:00 - 00:13:15 2%)."
            "All the timestamps in your response should always strictly follow this exact format with no variations permitted."
            "NEVER include timestamps in any other format"
            "each timestamp in this format should contain strictly only one start and end time"
            "The timestamp should ALWAYS be at the start of your paragraph"
            "Its imperitive that the timestamp range you provide is ALWAYS be a valid range that is taken directly from the video transcript that is provided to you such that the user can directly reference that point in the video."
            "any time you response contains a timestamp it should always be in the format specified above without any exception"
            "If your response contains multiple timestamps then combine the timestamps into one start to end timestamp that contains the entire answer. Ensure this timestamp is valid in the context of the video transcript."
            "Unless asked to elaborate or explain keep your answers consise while answering the query."
            "Your response should ALWAYS be relevant to the question asked and unless asked for never provide extra information"
            "Your answers must always be direct"
            "If you have not been provided any context then do not try to guess and provide an answer from the transcript but rather ask for more context to be provided in the prompt."
            "Always format your response such that each point is a new paragraph using the html <br> tag so that it can be displayed in a pretty way"
            "Do not mention the video ID, only the video Name should be mentioned."
        ),)
    else:
        if not os.path.exists("./llamaindex/global"):
            return None
        else:
            global_index = load_index_from_storage(
            StorageContext.from_defaults(persist_dir="./llamaindex/global"), index_id="global_vector_index"
            )
 
        chat_engine = global_index.as_chat_engine(chat_mode="condense_plus_context", verbose=True, llm=mistral,
                                        context_prompt=(
            "You are a video search chatbot. You operate with the collection of video transcripts that are provided to you."
            "Here are the relevant transcript for the video:\n"
            "{context_str}"
            "\nInstruction: Based on the provided documents, provide a detailed answer for the user question below."
            "Always Refer to the document as the video and avoid calling it a transcript."
            "Never mention or refer to any other video other than the ones in the provided transcript."
            "Always return only one video that you think is most relevant based on the user's question. If you cannot find any video that matches the requirement then simply say that there is no video that matches the requirement."
            "Never mention any file paths or file names, only the title of the video."
            "Never include any timestamp information in your response."
            "Unless asked to elaborate or explain ALWAYS keep your answers consise while answering the query."
            "Your response should ALWAYS be relevant to the question asked and always avoid giving unnecessary information"
            "If you have not been provided any context then do not try to guess and provide an answer from the transcript but rather ask for more context to be provided in the prompt."
            "Always format your response such that each point is a new paragraph using the html <br> tag so that it can be displayed in a pretty way"
        ),)
    return chat_engine

#getSummary returns the pre-generated summary for the video
def getSummary(videoId):
    Settings.llm = mistral
    Settings.embed_model = "local"
    if not os.path.exists("./llamaindex/"+videoId+"_summary"):
        return None
    else:
        summary_index = load_index_from_storage(
            StorageContext.from_defaults(persist_dir="./llamaindex/"+videoId+"_summary"),
        )
        return summary_index.get_document_summary(videoId)

# To test the module independently
# if __name__ == "__main__":
#     generateIndex("russianTale;;;;;;g3f_vi2-8Kk_01.vtt")
