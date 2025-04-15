# Voice Assistant

A voice-first interface application that allows for natural conversation with an AI assistant.

## Features
- Automatic voice activation upon startup
- Natural language conversation
- Text-to-speech responses
- Speech recognition for user input

## Setup

1. Install the required dependencies:
```bash
pip install -r requirements.txt
```

2. Create a `.env` file in the root directory and add your OpenAI API key:
```
OPENAI_API_KEY=your_openai_api_key_here
```

3. Run the application:
```bash
python voice_assistant.py
```

## Usage
- The assistant will greet you upon startup
- Speak naturally to interact with the assistant
- To exit, say "exit", "quit", "bye", or "goodbye"

## Requirements
- Python 3.7+
- Microphone
- Speakers
- OpenAI API key 