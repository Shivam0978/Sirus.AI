import os
import sys
import datetime
from google import genai
from google.genai import types
from dotenv import load_dotenv
import speech_recognition as sr
import pyttsx3

# Loading environment variables from .env file
load_dotenv()

# Getting the API key from the environment
api_key = os.environ.get("GEMINI_API_KEY")

if not api_key:
    print("Error: GEMINI_API_KEY not found in environment.")
    print("Please make sure you have created a .env file and added your API key.")
    print("Example: GEMINI_API_KEY=your_actual_api_key_here")
    sys.exit(1)


def speak(text):
    print(f"Sirus: {text}")
    try:
        # We initialize pyttsx3 INSIDE the function to fix a common Windows bug
        # where runAndWait() freezes or drops audio after the very first time it speaks.
        local_engine = pyttsx3.init()
        voices = local_engine.getProperty("voices")
        if len(voices) > 0:
            local_engine.setProperty("voice", voices[0].id)
        current_rate = local_engine.getProperty("rate")
        local_engine.setProperty("rate", current_rate + 25)

        # Strip markdown like ** or * that Gemini uses before speaking
        clean_text = text.replace("*", "").replace("#", "")
        local_engine.say(clean_text)
        local_engine.runAndWait()
    except Exception as e:
        print(f"Warning: Could not play audio: {e}")


# Initializing speech recognizer
recognizer = sr.Recognizer()
# Give you slightly more time to pause between words before cutting you off
recognizer.pause_threshold = 0.8
# Ensure automatic background noise levels adjustment(suggested by LLMs)
recognizer.dynamic_energy_threshold = True

# Initializing the client and model (using gemini-2.5-flash)
try:

    def get_greeting():
        hour = datetime.datetime.now().hour
        if hour < 12:
            return "Good morning sir."
        elif hour < 18:
            return "Good afternoon sir."
        else:
            return "Good evening sir."

    system_instruction = (
        f"Your name is Sirus. You are a personal AI assistant. "
        f"Whenever the user calls you 'Sirus' or greets you, you MUST reply with '{get_greeting()}' "
        f"and then address their request. Keep your responses conversational and concise, as they will be spoken out loud."
    )

    client = genai.Client(api_key=api_key)
    chat = client.chats.create(
        model="gemini-2.5-flash",
        config=types.GenerateContentConfig(system_instruction=system_instruction),
    )
except Exception as e:
    print(f"Error initializing the Gemini model: {e}")
    sys.exit(1)


def main():
    print("=" * 50)
    print("Welcome to your Voice Assistant, Sirus!")
    print("Press [Enter] to speak, OR type your question. Type 'quit' to end.")
    print("=" * 50)

    while True:
        try:
            user_input = input("\nPress [Enter] to talk, or type your message: ")

            # Check for exit commands
            if user_input.lower() in ["quit", "exit", "q"]:
                print("Sirus: Goodbye sir.")
                break

            is_voice_mode = False

            if not user_input.strip():
                # No text entered -> Voice mode
                is_voice_mode = True
                with sr.Microphone() as source:
                    recognizer.adjust_for_ambient_noise(source, duration=1.0)
                    print("Listening... (Speak now)")
                    audio = recognizer.listen(source)

                print("Processing voice...")
                try:
                    spoken_text = recognizer.recognize_google(audio)
                    print(f"You said: {spoken_text}")
                except sr.UnknownValueError:
                    print("(No voice detected)")
                    continue
                except sr.RequestError as e:
                    print(f"Could not request results; {e}")
                    continue
            else:
                # Text mode
                spoken_text = user_input.strip()

            # Skip if nothing was heard/typed
            if not spoken_text.strip():
                continue

            # Programmatic intercept for just calling "sirus"
            if spoken_text.strip().lower() in ["sirus", "cyrus"]:
                if is_voice_mode:
                    speak(f"Sirus activated. {get_greeting()}")
                else:
                    print(f"Sirus: Sirus activated. {get_greeting()}")
                continue

            print("Sirus is thinking...", end="\r")

            # Send the message to the model
            response = chat.send_message(spoken_text)

            # Clear the 'thinking' text
            print(" " * 20, end="\r")

            # Output response based on input mode
            if is_voice_mode:
                speak(response.text)
            else:
                print(f"Sirus: {response.text}")

        except KeyboardInterrupt:
            print("\n")
            speak("Goodbye sir.")
            break
        except Exception as e:
            print(f"\nAn error occurred while getting the response: {e}")


if __name__ == "__main__":
    main()
