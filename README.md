# Chat With Videos
LLM and Gen AI powered chat with video files

- **Privacy By Design:** Our solution prioritizes privacy by design, empowering users with self-hosted functionality and leveraging open-source technologies that allow for commercial use.
  
- **Language Agnostic Interaction:** Break down language barriers with our Large Language Model (LLM) powered chat, enabling access to knowledge across language barriers.
  
- **Comprehensive Search Capabilities:** Enjoy a global search feature that goes beyond titles, delving into the content of indexed videos for enhanced discoverability.
  
- **Context Aware Subtitles:** Generate and download context aware subtitles for videos in any language that are generated using a transformer model.
  
- **Efficient Navigation:** Navigate effortlessly through video content with timestamp hyperlinks embedded in all responses, facilitating swift access to relevant segments without having to watch the entire video.
  
- **Summarized Insights:** Gain quick insights with pre-generated video summaries featuring highlights for streamlining information consumption especially for long and information dense videos.
  
- **Adaptability and Integration:** Seamlessly integrate with different LLM models and video platforms, offering a plug-and-play solution tailored to your needs.


## Installation
1. Clone the repository
2. Install the required packages using pip. 
`pip install -r requirements.txt`
3. Make sure Ollama is installed and running. 
`curl -fsSL https://ollama.com/install.sh | sh`
4. Make sure Ollama has the model you need.
`ollama pull llama3`
5. Run the app. 
`python server.py`
6. By default the app will run on port `2020`.

To setup whisper.cpp clone the repository into the current folder and follow the instructions to build the library.
https://github.com/ggerganov/whisper.cpp


