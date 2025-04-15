from flask import Flask, render_template, jsonify, request
from voice_assistant import VoiceAssistant
import threading
import queue
import logging
import time

# Configure logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

app = Flask(__name__)
assistant = None
message_queue = queue.Queue()
is_listening = False
assistant_thread_instance = None  # Track the assistant thread

def assistant_thread():
    global is_listening
    logger.debug("Assistant thread started")
    while is_listening:
        try:
            # Only listen if the assistant is not speaking
            if not assistant.is_speaking:
                logger.debug("Listening for user input...")
                user_input, is_error = assistant.listen()  # Now returns a tuple
                logger.debug(f"User input received: {user_input}")
                
                if user_input.lower() in ['exit', 'quit', 'bye', 'goodbye']:
                    message_queue.put(('assistant', 'Goodbye! Have a great day!'))
                    is_listening = False
                    break
                
                if not is_error:  # Only get AI response if there was no error
                    logger.debug("Getting AI response...")
                    response = assistant.get_ai_response(user_input)
                    logger.debug(f"AI response: {response}")
                    message_queue.put(('assistant', response))
                    
                    assistant.speak(response, force_tts=True)
                else:
                    # Just speak the error message directly
                    message_queue.put(('error', user_input))
                    assistant.speak(user_input, force_tts=True)
            else:
                # Small sleep to prevent CPU spinning while waiting for speech to end
                time.sleep(0.1)
        except Exception as e:
            logger.error(f"Error in assistant thread: {str(e)}")
            message_queue.put(('error', f"Error: {str(e)}"))

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/start', methods=['POST'])
def start():
    global is_listening, assistant_thread_instance, assistant
    logger.debug("Start endpoint called")
    
    try:
        data = request.get_json()
        voice = data.get('voice', 'Daniel')  # Using Whisper as the default voice
        
        # Initialize assistant with selected voice
        assistant = VoiceAssistant(voice=voice)
        
        if not is_listening:
            is_listening = True
            if assistant_thread_instance is None or not assistant_thread_instance.is_alive():
                assistant_thread_instance = threading.Thread(target=assistant_thread, daemon=True)
                assistant_thread_instance.start()
                logger.debug("Assistant thread started")
                return jsonify({'status': 'started'})
        return jsonify({'status': 'already running'})
    except Exception as e:
        logger.error(f"Error starting assistant: {str(e)}")
        return jsonify({'status': 'error', 'message': str(e)})

@app.route('/stop', methods=['POST'])
def stop():
    global is_listening, assistant_thread_instance
    logger.debug("Stop endpoint called")
    is_listening = False
    if assistant_thread_instance and assistant_thread_instance.is_alive():
        assistant_thread_instance.join(timeout=2)  # Wait for thread to finish
    assistant_thread_instance = None
    return jsonify({'status': 'stopped'})

@app.route('/stop_speaking', methods=['POST'])
def stop_speaking():
    global assistant
    try:
        if assistant:
            assistant.stop_speaking()
            return jsonify({'status': 'stopped'})
        return jsonify({'status': 'error', 'message': 'Assistant not initialized'})
    except Exception as e:
        logger.error(f"Error stopping speech: {str(e)}")
        return jsonify({'status': 'error', 'message': str(e)})

@app.route('/pause', methods=['POST'])
def pause():
    global assistant
    try:
        if assistant:
            assistant.pause()
            return jsonify({'status': 'paused'})
        return jsonify({'status': 'error', 'message': 'Assistant not initialized'})
    except Exception as e:
        logger.error(f"Error pausing: {str(e)}")
        return jsonify({'status': 'error', 'message': str(e)})

@app.route('/resume', methods=['POST'])
def resume():
    global assistant
    try:
        if assistant:
            assistant.resume()
            return jsonify({'status': 'resumed'})
        return jsonify({'status': 'error', 'message': 'Assistant not initialized'})
    except Exception as e:
        logger.error(f"Error resuming: {str(e)}")
        return jsonify({'status': 'error', 'message': str(e)})

@app.route('/messages')
def get_messages():
    messages = []
    while not message_queue.empty():
        message = message_queue.get()
        logger.debug(f"Retrieved message: {message}")
        messages.append(message)
    return jsonify({'messages': messages})

if __name__ == '__main__':
    app.run(debug=False, port=3002)  # Disabled debug mode to prevent multiple instances 