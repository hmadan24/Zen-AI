import speech_recognition as sr
import openai
import os
import platform
import subprocess
from dotenv import load_dotenv
import sys
import time
import threading
import logging

# Configure logging
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    stream=sys.stdout
)
logger = logging.getLogger(__name__)

# Load environment variables
load_dotenv()

# Verify OpenAI API key
api_key = os.getenv('OPENAI_API_KEY')
if not api_key:
    logger.error("Error: OPENAI_API_KEY not found in environment variables")
    sys.exit(1)

# Initialize OpenAI client
try:
    # Remove any proxy environment variables that might interfere
    if 'HTTP_PROXY' in os.environ:
        del os.environ['HTTP_PROXY']
    if 'HTTPS_PROXY' in os.environ:
        del os.environ['HTTPS_PROXY']
    
    # Initialize client with minimal configuration and explicit proxy settings
    client = openai.OpenAI(
        api_key=api_key,
        base_url="https://api.openai.com/v1"  # Explicitly set the base URL
    )
    logger.info("OpenAI client initialized successfully")
except Exception as e:
    logger.error(f"Error initializing OpenAI client: {str(e)}")
    logger.error(f"Error type: {type(e)}")
    logger.error(f"Error args: {e.args}")
    sys.exit(1)

class VoiceAssistant:
    def __init__(self, voice='Daniel'):
        try:
            self.recognizer = sr.Recognizer()
            # Initialize conversation history
            self.conversation_history = [
                {"role": "system", "content": "You are a helpful voice assistant. Keep responses concise and conversational. Avoid repeating the same responses."}
            ]
            # Add flag to track if assistant is speaking
            self.is_speaking = False
            self.is_paused = False
            self.current_speech_process = None
            # Add minimum silence duration after speaking
            self.silence_duration = 0.3  # seconds
            # Store selected voice
            self.voice = voice
            print("Speech recognizer initialized")
            
            # Print available microphones
            print("\nChecking available microphones...")
            try:
                mic_names = sr.Microphone.list_microphone_names()
                if not mic_names:
                    print("Warning: No microphones found")
                else:
                    print("Available microphones:")
                    for index, name in enumerate(mic_names):
                        print(f"Microphone {index}: {name}")
                    
                    # Try to find the best microphone
                    best_mic_index = None
                    for index, name in enumerate(mic_names):
                        if "microphone" in name.lower():
                            best_mic_index = index
                            break
                    
                    self.mic_index = best_mic_index
                    if best_mic_index is not None:
                        print(f"\nSelected microphone: {mic_names[best_mic_index]}")
                    else:
                        print("\nUsing default microphone")
            except Exception as e:
                print(f"Error listing microphones: {str(e)}")
                self.mic_index = None
                print("\nUsing default microphone")
            
            # Check if text-to-speech is available
            self.tts_available = self._check_tts_availability()
            
        except Exception as e:
            print(f"Error in VoiceAssistant initialization: {str(e)}")
            sys.exit(1)
    
    def _check_tts_availability(self):
        """Check if text-to-speech is available on the system"""
        try:
            if platform.system() == 'Darwin':  # macOS
                # Try to run a simple say command
                subprocess.run(['say', '-v', '?'], capture_output=True, text=True)
                return True
            return False
        except Exception:
            return False

    def _wait_for_speech_end(self, process):
        """Wait for the speech process to complete"""
        process.wait()
        time.sleep(self.silence_duration)  # Add extra silence
        self.is_speaking = False
    
    def stop_speaking(self):
        """Stop the current speech"""
        if self.current_speech_process and self.current_speech_process.poll() is None:
            self.current_speech_process.terminate()
            self.is_speaking = False
            self.current_speech_process = None

    def pause(self):
        """Pause both listening and speaking"""
        self.is_paused = True
        self.stop_speaking()

    def resume(self):
        """Resume both listening and speaking"""
        self.is_paused = False

    def speak(self, text, force_tts=False):
        """Convert text to speech using macOS say command with enhanced voice options"""
        print(f"Assistant: {text}")  # Always print the response
        try:
            if platform.system() == 'Darwin' and (self.tts_available or force_tts):  # macOS
                self.is_speaking = True
                print(f"Using voice: {self.voice}")  # Debug log
                # Use the selected voice with enhanced speech parameters
                self.current_speech_process = subprocess.Popen([
                    'say',
                    '-v', self.voice,
                    '-r', '175',    # Natural speaking rate
                    text
                ])
                # Start a thread to wait for speech end
                threading.Thread(target=self._wait_for_speech_end, args=(self.current_speech_process,), daemon=True).start()
            else:
                print("Text-to-speech not supported or not available in this context")
        except Exception as e:
            print(f"Error in text-to-speech: {str(e)}")
            print("Continuing in text-only mode")
            self.is_speaking = False
        
    def listen(self):
        """Listen for user input"""
        try:
            # Wait until the assistant is not speaking and not paused
            while self.is_speaking or self.is_paused:
                time.sleep(0.1)
            
            mic = sr.Microphone(device_index=self.mic_index) if self.mic_index is not None else sr.Microphone()
            
            with mic as source:
                print("Adjusting for ambient noise...")
                self.recognizer.adjust_for_ambient_noise(source, duration=0.5)
                print("Listening...")
                audio = self.recognizer.listen(source, timeout=10, phrase_time_limit=15)
                print("Audio captured, processing...")
                
            try:
                print("Recognizing...")
                text = self.recognizer.recognize_google(audio, language="en-US")
                print(f"User said: {text}")
                return text, False
            except sr.UnknownValueError:
                print("Google Speech Recognition could not understand audio")
                return "Sorry, I couldn't understand that. Could you please speak more clearly?", True
            except sr.RequestError as e:
                print(f"Could not request results from Google Speech Recognition service; {e}")
                return "Sorry, there was an error with the speech recognition service. Please try again.", True
        except Exception as e:
            print(f"Error in listening: {str(e)}")
            return "Sorry, there was an error with the microphone. Please check your microphone settings.", True
            
    def get_ai_response(self, user_input):
        """Get response from OpenAI"""
        try:
            # Add user's message to conversation history
            self.conversation_history.append({"role": "user", "content": user_input})
            
            # Keep only the last 5 exchanges to maintain context without making the context too long
            if len(self.conversation_history) > 11:  # system message + 5 exchanges (10 messages)
                self.conversation_history = [self.conversation_history[0]] + self.conversation_history[-10:]
            
            response = client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=self.conversation_history
            )
            
            assistant_response = response.choices[0].message.content
            # Add assistant's response to conversation history
            self.conversation_history.append({"role": "assistant", "content": assistant_response})
            
            return assistant_response
        except Exception as e:
            return f"Sorry, I encountered an error: {str(e)}"
            
    def run(self):
        """Main loop for the voice assistant"""
        # Initial greeting
        greeting = "Hello! I'm your voice assistant. How can I help you today?"
        print(greeting)
        self.speak(greeting)
        
        while True:
            user_input, is_error = self.listen()
            if is_error:
                print("Error in listening, skipping response")
                continue
            if user_input.lower() in ['exit', 'quit', 'bye', 'goodbye']:
                farewell = "Goodbye! Have a great day!"
                print(farewell)
                self.speak(farewell)
                break
                
            response = self.get_ai_response(user_input)
            print(f"Assistant: {response}")
            self.speak(response)

if __name__ == "__main__":
    assistant = VoiceAssistant()
    assistant.run() 