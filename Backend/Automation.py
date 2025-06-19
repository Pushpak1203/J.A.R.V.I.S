# Import all the necessary libraries
from AppOpener import close, open as openApp
from webbrowser import open as webopen
from pywhatkit import search, playonyt
from dotenv import dotenv_values
from bs4 import BeautifulSoup
from rich import print
from groq import Groq
import webbrowser
import subprocess
import requests
import keyboard
import asyncio
import os

# Load the environment variables from the .env file
env_vars = dotenv_values(".env")
GroqAPIKey = env_vars["GroqAPIKey"]

# Define CSS classes for passing specific elements in HTML content.
classes = ["zCubwf", "hgKElc", "LTKOO SY7ric", "ZOLcW", "gsrt vk_bk FzvWSb YwPhnf", "pclqee", "tw-Data-text tw-text-small tw-ta",
           "IZ6rdc", "05uR6d LTKOO", "vlzY6d", "webanswers-webanswers_table_webanswers-table", "dDoNo ikb4Bb gsrt", "sXLaOe",
           "LWkfKe", "VQF4g", "qv3Wpe", "kno-rdesc", "SPZz6b"]

# Define a user-agent for making web requests.
useragent = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/58.0.3029.110 Safari/537.3"

# Initialize the Groq client with the API key.
client = Groq(api_key=GroqAPIKey)

# Predefined professional responses.
professional_responses = [
    "Your satisfaction is my top priority; feel free reach to out if there's anything else I can help you with.",
    "I'm at your service for any additional questions or suport you may need-don't hesitate to ask.",
]

# List to store chatbot messages.
messages = []

# System message to provide context to the chatbot.
SystemChatBot = [{"role": "system", "content": f"Hello, I am {os.environ.get('Username', 'ContentWriter')}, You're content writer. You have to write content like letter."}]

# Function to perform a Google search.
def GoogleSearch(Topic):
    try:
        search(Topic)
        print(f"Google search executed for: {Topic}")
        return True
    except Exception as e:
        print(f"Error in GoogleSearch: {e}")
        return False

# Function to generate content using AI and save it to a file.
def Content(Topic):

    # Nested function to open a file in Notepad.
    def OpenNotepad(File):
        try:
            default_text_editor = 'notepad.exe'
            subprocess.Popen([default_text_editor, File])
            print(f"Opened {File} in Notepad")
            return True
        except Exception as e:
            print(f"Error opening Notepad: {e}")
            return False

    # Nested function to generate content using AI chatbot.
    def ContentWriterAI(Topic):
        try:
            messages.append({"role": "user", "content": f"{Topic}"})

            completions = client.chat.completions.create(
                model="mixtral-8x7b-32768",
                messages=SystemChatBot + messages,
                max_tokens=2048,
                temperature=0.7,
                top_p=1,
                stream=False,  # Changed to False for non-streaming
                stop=None
            )

            Answer = completions.choices[0].message.content  # Access content directly

            Answer = Answer.replace("</s>", "")
            messages.append({"role": "assistant", "content": Answer})  # Use the actual answer
            return Answer
        except Exception as e:
            print(f"Error in ContentWriterAI: {e}")
            return f"Error generating content: {e}"

    try:
        Topic = Topic.replace("content", "").strip()  # Remove "content" and strip whitespace
        ContentByAI = ContentWriterAI(Topic)

        # Save the generated content to a text file.
        filename = f"Data{Topic.lower().replace(' ', '')}.txt"
        filepath = os.path.join("Data", filename)  # Construct the full file path
        os.makedirs("Data", exist_ok=True)  # Ensure the "Data" directory exists

        with open(filepath, 'w', encoding='utf-8') as file:  # Use 'w' mode to overwrite
            file.write(ContentByAI)

        OpenNotepad(filepath)
        print(f"Content generated and saved to: {filepath}")
        return True
    except Exception as e:
        print(f"Error in Content function: {e}")
        return False

# Function to search for a topic on YouTube.
def YouTubeSearch(Topic):
    try:
        Url4Search = f"https://www.youtube.com/results?search_query={Topic}"
        webbrowser.open(Url4Search)
        print(f"YouTube search executed for: {Topic}")
        return True
    except Exception as e:
        print(f"Error in YouTubeSearch: {e}")
        return False

# Function to play a video on YouTube.
def PlayYoutube(query):
    try:
        playonyt(query)
        print(f"Playing on YouTube: {query}")
        return True
    except Exception as e:
        print(f"Error in PlayYoutube: {e}")
        return False

# Function to open an application or relevant webpages.
def OpenApp(app, sess=requests.session()):
    try:
        print(f"Attempting to open app: {app}")
        openApp(app, match_closest=True, output=True, throw_error=True)
        print(f"Successfully opened app: {app}")
        return True

    except Exception as e:
        print(f"Error opening app using AppOpener: {e}")
        print(f"Trying alternative method for: {app}")

        # Nested function to extract links from HTML content.
        def extract_links(html):
            if html is None:
                return []
            soup = BeautifulSoup(html, "html.parser")
            links = soup.find_all('a', {'jsname': 'UWckNb'})
            extracted_links = [link.get('href') for link in links if link.get('href')]
            return extracted_links

        # Nested function to perform a Google search and retrieve HTML.
        def search_google(query):
            try:
                url = f"https://www.google.com/search?q={query}"
                headers = {"User-Agent": useragent}
                response = sess.get(url, headers=headers)

                if response.status_code == 200:
                    return response.text
                else:
                    print(f"Failed to retrieve search results. Status code: {response.status_code}")
                return None
            except Exception as e:
                print(f"Error in search_google: {e}")
                return None

        try:
            html = search_google(f"{app} download")
            if html:
                links = extract_links(html)
                if links:
                    webopen(links[0])
                    print(f"Opened web link for: {app}")
                    return True
                else:
                    print(f"No links found for: {app}")
                    return False
            else:
                print(f"Could not get search results for: {app}")
                return False
        except Exception as e:
            print(f"Error in alternative app opening method: {e}")
            return False

# Function to close an application.
def CloseApp(app):
    try:
        if "chrome" in app.lower():
            print("Chrome close request - handling specially")
            # You might want to add specific Chrome closing logic here
            return True
        else:
            close(app, match_closest=True, output=True, throw_error=True)
            print(f"Successfully closed app: {app}")
            return True
    except Exception as e:
        print(f"Error closing app {app}: {e}")
        return False

# Function to execute system-level commands.
def System(command):
    try:
        # Nested function to mute the system volume.
        def mute():
            keyboard.press_and_release("volume mute")
            print("System muted")

        # Nested function to unmute the system volume.
        def unmute():
            keyboard.press_and_release("volume mute")
            print("System unmuted")

        # Nested function to increase the system volume.
        def volume_up():
            keyboard.press_and_release("volume up")
            print("Volume increased")

        # Nested function to decrease the system volume.
        def volume_down():
            keyboard.press_and_release("volume down")
            print("Volume decreased")

        # Execute the appropriate system command.
        command = command.lower().strip()
        if "mute" in command and "unmute" not in command:
            mute()
        elif "unmute" in command:
            unmute()  
        elif "volume up" in command or "increase volume" in command:
            volume_up()
        elif "volume down" in command or "decrease volume" in command:
            volume_down()
        else:
            print(f"Unknown system command: {command}")
            return False
        return True
    except Exception as e:
        print(f"Error in System function: {e}")
        return False

# Function to execute individual commands
def ExecuteCommand(command):
    """Execute a single command and return success status"""
    try:
        command = command.lower().strip()
        print(f"Executing command: {command}")

        if command.startswith("open"):
            app_name = command.replace("open", "").strip()
            if app_name and app_name not in ["it", "file"]:
                return OpenApp(app_name)
            else:
                print("Invalid app name for open command")
                return False

        elif command.startswith("close"):
            app_name = command.replace("close", "").strip()
            if app_name:
                return CloseApp(app_name)
            else:
                print("Invalid app name for close command")
                return False

        elif command.startswith("play"):
            query = command.replace("play", "").strip()
            if query:
                return PlayYoutube(query)
            else:
                print("Invalid query for play command")
                return False

        elif command.startswith("content"):
            topic = command.replace("content", "").strip()
            if topic:
                return Content(topic)
            else:
                print("Invalid topic for content command")
                return False

        elif command.startswith("google search"):
            topic = command.replace("google search", "").strip()
            if topic:
                return GoogleSearch(topic)
            else:
                print("Invalid topic for google search command")
                return False

        elif command.startswith("youtube search"):
            topic = command.replace("youtube search", "").strip()
            if topic:
                return YouTubeSearch(topic)
            else:
                print("Invalid topic for youtube search command")
                return False

        elif command.startswith("system"):
            system_command = command.replace("system", "").strip()
            if system_command:
                return System(system_command)
            else:
                print("Invalid system command")
                return False

        else:
            print(f"Unknown command format: {command}")
            return False

    except Exception as e:
        print(f"Error executing command '{command}': {e}")
        return False

# Main automation function - FIXED VERSION
def Automation(commands):
    """
    Execute automation commands synchronously
    Args:
        commands: Can be a single command string or list of command strings
    Returns:
        bool: True if all commands executed successfully, False otherwise
    """
    try:
        # Handle both single command and list of commands
        if isinstance(commands, str):
            commands = [commands]
        elif not isinstance(commands, list):
            print(f"Invalid commands type: {type(commands)}")
            return False

        print(f"Starting automation with commands: {commands}")
        
        results = []
        for command in commands:
            if command and command.strip():
                result = ExecuteCommand(command.strip())
                results.append(result)
                print(f"Command '{command}' executed with result: {result}")
            else:
                print(f"Skipping empty command: {command}")
                results.append(False)

        # Return True if all commands succeeded
        success = all(results) if results else False
        print(f"Automation completed. Overall success: {success}")
        return success

    except Exception as e:
        print(f"Error in Automation function: {e}")
        return False

# Legacy async function for backward compatibility
async def TranslateAndExecute(commands: list[str]):
    """Legacy async function - now calls the synchronous version"""
    try:
        result = Automation(commands)
        yield result
    except Exception as e:
        print(f"Error in TranslateAndExecute: {e}")
        yield False