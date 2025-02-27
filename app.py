import time
import jwt
import streamlit as st
import asyncio
import requests
import speech_recognition as sr
import re
import pyttsx3
import threading
import openai
from livekit.agents import AutoSubscribe, JobContext
from livekit.rtc import Room, RoomOptions
from PIL import Image

# LiveKit Server Details
LIVEKIT_URL = "wss://voice-chat-em3qvvl2.livekit.cloud"
API_KEY = "APIRiqaMhPvtXyt"
API_SECRET = "lfpveQi875IqUIyleBA0YQKE7Llzjg7MjImkEAk3iTvA"

# Load Images
image = Image.open("/home/sriram/Downloads/logo.png")
image1 = Image.open("/home/sriram/Downloads/logo1.png")

# Create two columns to align images side by side
col1, col2 = st.columns([1, 1])  
with col1:
    st.image(image, width=300)
with col2:
    st.image(image1, width=300)

st.title("AI ASSISTANT")
st.write("Speak or text to chat with Optimus in real-time!")

# Initialize text-to-speech engine
engine = pyttsx3.init()
engine.setProperty("rate", 120)  
engine.setProperty("volume", 1.0)

# Set Female Voice if available
voices = engine.getProperty("voices")
for voice in voices:
    if "female" in voice.name.lower():
        engine.setProperty("voice", voice.id)
        break

# Function to generate LiveKit JWT token
def generate_token(room_name, identity):
    payload = {
        "exp": int(time.time()) + 3600,  # Token valid for 1 hour
        "iss": API_KEY,
        "sub": identity,
        "video": {
            "room": room_name,
            "canPublish": True,
            "canSubscribe": True
        }
    }
    return jwt.encode(payload, API_SECRET, algorithm="HS256")

# Function to join LiveKit room
async def join_room(user_id):
    room_name = f"voice-chatbot-{user_id}"  # Unique room for each user
    token = generate_token(room_name, user_id)

    try:
        room = Room()
        await room.connect(LIVEKIT_URL, token)
        st.success(f"Successfully joined your private chat room: {room_name}")
    except Exception as e:
        st.error(f"Error joining LiveKit Room: {e}")

# Function to run the async join_room in a separate thread
def run_join_room(user_id):
    asyncio.run(join_room(user_id))

# Function to get user voice input with noise reduction
def get_voice_input():
    recognizer = sr.Recognizer()
    recognizer.energy_threshold = 300  # Reduce background noise
    recognizer.dynamic_energy_threshold = True  # Adjust sensitivity

    with sr.Microphone() as source:
        st.info("🎤 Speak now...")
        try:
            audio = recognizer.listen(source, timeout=5, phrase_time_limit=10)
            text = recognizer.recognize_google(audio)
            st.write(f"**You:** {text}")
            return text
        except sr.UnknownValueError:
            st.error("Could not understand your voice. Try speaking clearly.")
            return None
        except sr.RequestError:
            st.error("Speech recognition request failed. Check your internet connection.")
            return None

# Function to clean AI response
def clean_response(response):
    response = re.sub(r"[*_]", "", response)
    response = re.sub(r"\s+", " ", response).strip()
    return response

# Function to get AI response dynamically from API
def get_ai_response(user_input):
    try:
        CHATBOT_API_URL = "http://204.12.227.152:8000/chatbot/send_message"

        # Get all URL query parameters dynamically
        query_params = st.query_params
        extracted_params = {"message": user_input}  # Include user message

        # Iterate dynamically over all provided query parameters
        for key, value in query_params.items():
            extracted_params[key] = value[0] if isinstance(value, list) else value  # Handle list values

        # Display extracted parameters for debugging
        st.write("Extracted Parameters:")
        for key, value in extracted_params.items():
            st.write(f"{key}: {value}")

        print("params---", extracted_params)

        headers = {"accept": "application/json"}

        # Make the API call
        response = requests.post(CHATBOT_API_URL, headers=headers, params=extracted_params)
        print("response", response)

        if response.status_code == 200:
            response_data = response.json()
            cleaned_response = clean_response(response_data.get("actual_response", "No response received."))
            return cleaned_response
        else:
            return f"Error: Received status code {response.status_code}"
    except Exception as e:
        return f"Error contacting chatbot API: {e}"

# Function to stream AI voice response
def speak_response(response_text):
    engine.say(response_text)
    engine.runAndWait()
    st.write(f"**AI :** {response_text}")
    print(response_text)

# Text input for user
user_input = st.text_input("Type your message or use voice:")

# Voice input button
if st.button("🎙️ Speak"):
    voice_text = get_voice_input()
    if voice_text:
        user_input = voice_text

# Process AI response
if user_input:
    ai_response = get_ai_response(user_input)
    if ai_response:
        speak_response(ai_response)
