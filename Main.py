import json
import os
import subprocess
import threading
import sys
import asyncio
from time import sleep

from dotenv import dotenv_values
from Frontend.GUI import (
    GraphicalUserInterface,
    SetAssistantStatus,
    ShowTextToScreen,
    TempDirectoryPath,
    SetMicrophoneStatus,
    AnswerModifier,
    QueryModifier,
    GetMicrophoneStatus,
    GetAssistantStatus,
)
from Backend.Model import FirstLayerDMM
from Backend.RealTimeSearchEngine import RealTimeSearchEngine
from Backend.Automation import Automation as BackendAutomation
from Backend.SpeechToText import SpeechRecognition
from Backend.Chatbot import ChatBot
from Backend.TextToSpeech import TextToSpeech

# Load environment variables
env_vars = dotenv_values(".env")
Username = env_vars.get("Username", "User")
Assistantname = env_vars.get("Assistantname", "Assistant")

DATA_DIR = 'Data'
FRONTEND_FILES_DIR = os.path.join('Frontend', 'Files')

DefaultMessage = f"""{Username}: Hello {Assistantname}, How are you?
{Assistantname}: Welcome {Username}, I am doing great, How can I help you?"""

subprocesses = []

# Enhanced Functions list with common variations
Functions = [
    "open", "close", "play", "system", "content", 
    "google search", "youtube", "youtube search", "generate image", 
    "reminder", "volume up", "volume down", "mute"
]

# Automation keywords for fallback detection
automation_keywords = {
    "play": ["play", "start playing", "put on", "stream"],
    "open": ["open", "launch", "start", "run"],
    "close": ["close", "shut", "exit", "quit"],
    "youtube": ["youtube", "yt", "video", "watch"],
    "google search": ["search", "google", "find", "look up"],
    "volume": ["volume", "sound", "audio"],
    "system": ["system", "computer", "pc"],
    "reminder": ["remind", "reminder", "schedule", "alert"]
}

def detect_automation_intent(query):
    """
    Enhanced automation detection that checks for keywords and patterns
    """
    query_lower = query.lower()
    
    # Check for YouTube-related queries
    if any(word in query_lower for word in ["youtube", "video", "watch", "song", "music"]):
        if any(word in query_lower for word in ["play", "start", "put on", "stream"]):
            return f"play {query}"
    
    # Check for other automation patterns
    for action, keywords in automation_keywords.items():
        if any(keyword in query_lower for keyword in keywords):
            return f"{action} {query}"
    
    # Check if query starts with automation verbs
    for func in Functions:
        if query_lower.startswith(func.lower()):
            return query
    
    return None

def ShowDefaultChatIfNoChats():
    try:
        chatlog_path = os.path.join(DATA_DIR, 'chatlog.json')
        os.makedirs(DATA_DIR, exist_ok=True)

        with open(chatlog_path, "r", encoding="utf-8") as file:
            content = file.read().strip()
            if len(content) < 5 or not content:
                open(TempDirectoryPath('Database.data'), 'w', encoding='utf-8').close()
                open(TempDirectoryPath('Responses.data'), 'w', encoding='utf-8').close()
                if not content:
                    with open(chatlog_path, 'w', encoding='utf-8') as f:
                        json.dump([{"role": "user", "content": f"Hello {Assistantname}"},
                                    {"role": "assistant", "content": f"Welcome {Username}, I am doing great, How can I help you?"}], f, indent=4)
    except FileNotFoundError:
        print("Chatlog.json not found. Initializing chat files.")
        os.makedirs(DATA_DIR, exist_ok=True)
        with open(chatlog_path, 'w', encoding='utf-8') as f:
            json.dump([{"role": "user", "content": f"Hello {Assistantname}"},
                       {"role": "assistant", "content": f"Welcome {Username}, I am doing great, How can I help you?"}], f, indent=4)
        open(TempDirectoryPath('Database.data'), 'w', encoding='utf-8').close()
        open(TempDirectoryPath('Responses.data'), 'w', encoding='utf-8').close()
    except json.JSONDecodeError:
        print("Chatlog.json is corrupted. Resetting.")
        with open(chatlog_path, 'w', encoding='utf-8') as f:
            json.dump([{"role": "user", "content": f"Hello {Assistantname}"},
                       {"role": "assistant", "content": f"Welcome {Username}, I am doing great, How can I help you?"}], f, indent=4)
        open(TempDirectoryPath('Database.data'), 'w', encoding='utf-8').close()
        open(TempDirectoryPath('Responses.data'), 'w', encoding='utf-8').close()

def ReadChatLogJson():
    try:
        with open(os.path.join(DATA_DIR, 'Chatlog.json'), "r", encoding="utf-8") as file:
            return json.load(file)
    except (FileNotFoundError, json.JSONDecodeError):
        return []

def SaveChatLogJson(data):
    try:
        os.makedirs(DATA_DIR, exist_ok=True)
        with open(os.path.join(DATA_DIR, 'Chatlog.json'), "w", encoding="utf-8") as file:
            json.dump(data, file, indent=4)
    except IOError as e:
        print(f"Error saving chatlog.json: {e}")

def ChatLogIntegration():
    json_data = ReadChatLogJson()
    formatted_chatlog = "\n".join(
        f"{Username if entry['role'] == 'user' else Assistantname}: {entry['content']}"
        for entry in json_data
    )
    try:
        with open(TempDirectoryPath('Database.data'), 'w', encoding='utf-8') as file:
            file.write(AnswerModifier(formatted_chatlog))
    except IOError as e:
        print(f"Error writing to Database.data: {e}")

def ShowChatsOnGUI():
    try:
        with open(TempDirectoryPath('Database.data'), 'r', encoding='utf-8') as file:
            data = file.read().strip()
        if data:
            with open(TempDirectoryPath('Responses.data'), 'w', encoding='utf-8') as file:
                file.write(data)
    except FileNotFoundError:
        print("Database.data not found during GUI chat display.")
    except IOError as e:
        print(f"Error writing to Responses.data for GUI display: {e}")

def InitialExecution():
    SetMicrophoneStatus("False")
    ShowTextToScreen("")
    ShowDefaultChatIfNoChats()
    ChatLogIntegration()
    ShowChatsOnGUI()

InitialExecution()

background_async_loop = None

def run_async_in_thread(coro):
    if background_async_loop and background_async_loop.is_running():
        future = asyncio.run_coroutine_threadsafe(coro, background_async_loop)
        return future.result()
    else:
        print("Error: Background async loop is not running. Cannot execute async task.")
        return False

def _extract_parenthesized_query(command_string):
    """Extracts the content within parentheses if present, otherwise returns the whole string."""
    start = command_string.find('(')
    end = command_string.rfind(')')
    if start != -1 and end != -1 and end > start:
        return command_string[start + 1:end].strip()
    return command_string.strip()

async def process_user_query_async(query):
    print(f"User Query (async): {query}")
    
    SetAssistantStatus("Thinking...")
    Decision = await asyncio.to_thread(FirstLayerDMM, query)
    print(f"Decision from Model.py (async): {Decision}")

    # Handle empty or invalid decisions
    if not Decision or Decision == [""]:
        print("Empty decision from model, falling back to automation detection")
        automation_intent = detect_automation_intent(query)
        if automation_intent:
            Decision = [automation_intent]
        else:
            Decision = [f"general {query}"]

    automation_commands_to_execute = []
    general_or_realtime_queries = []
    
    for item in Decision:
        item_lower = item.lower()
        original_query_lower = query.lower()

        # Handle generate image commands
        if item_lower.startswith("generate image"):
            ImageGenerationQuery = item
            image_generation_path = TempDirectoryPath('ImageGeneration.data')
            try:
                os.makedirs(os.path.dirname(image_generation_path), exist_ok=True) 
                with open(image_generation_path, "w") as file:
                    file.write(f"{ImageGenerationQuery},True")
                
                print(f"Starting ImageGeneration.py with query: {ImageGenerationQuery}")
                p1 = subprocess.Popen(
                    [sys.executable, os.path.join('Backend', 'ImageGeneration.py')],
                    stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                    stdin=subprocess.PIPE, shell=False
                )
                subprocesses.append(p1)
            except Exception as e:
                print(f"Error Starting ImageGeneration.py: {e}")

        # Check if it's an automation command
        elif any(item_lower.startswith(func.lower()) for func in Functions):
            automation_commands_to_execute.append(item)
            print(f"Identified automation command: {item}")

        # Handle general queries that might be misclassified automation
        elif item_lower.startswith("general"):
            # Extract the actual query content
            general_content = _extract_parenthesized_query(item.removeprefix("general"))
            
            # Check if this general query should actually be automation
            automation_intent = detect_automation_intent(general_content)
            if automation_intent:
                print(f"Reclassifying general query as automation: {general_content} -> {automation_intent}")
                automation_commands_to_execute.append(automation_intent)
            else:
                general_or_realtime_queries.append(item)
                print(f"Identified general query: {item}")

        elif item_lower.startswith("realtime"):
            general_or_realtime_queries.append(item)
            print(f"Identified realtime query: {item}")
        
        elif "exit" in item_lower:
            SetAssistantStatus("Answering...")
            ShowTextToScreen(f"{Assistantname}: Okay, Bye!")
            TextToSpeech("Okay, Bye!")
            print("Exiting application as requested.")
            sys.exit(0)
        else:
            # If we can't classify it, try automation detection as fallback
            automation_intent = detect_automation_intent(item)
            if automation_intent:
                print(f"Fallback automation detection: {item} -> {automation_intent}")
                automation_commands_to_execute.append(automation_intent)
            else:
                print(f"Warning: Decision item not explicitly handled: {item}")
                # Treat as general query
                general_or_realtime_queries.append(f"general {item}")

    # Execute automation commands - FIXED VERSION
    if automation_commands_to_execute:
        print(f"Executing automation commands: {automation_commands_to_execute}")
        SetAssistantStatus("Performing Task...")
        
        try:
            # Handle automation commands - FIXED: Call Automation directly
            success = await asyncio.to_thread(BackendAutomation, automation_commands_to_execute)
            
            if success:
                print(f"All automation tasks completed successfully")
                # Provide feedback to user
                if len(automation_commands_to_execute) == 1:
                    response = f"Task completed: {automation_commands_to_execute[0]}"
                else:
                    response = f"All {len(automation_commands_to_execute)} tasks completed successfully"
                    
                current_chat_log.append({"role": "assistant", "content": response})
                SaveChatLogJson(current_chat_log)
                ShowTextToScreen(f"{Assistantname}: {response}")
                ChatLogIntegration()
                ShowChatsOnGUI()
                SetAssistantStatus("Answering...")
                await asyncio.to_thread(TextToSpeech, response)
            else:
                print(f"Some automation tasks failed")
                error_response = "I completed some tasks, but encountered issues with others."
                current_chat_log.append({"role": "assistant", "content": error_response})
                SaveChatLogJson(current_chat_log)
                ShowTextToScreen(f"{Assistantname}: {error_response}")
                ChatLogIntegration()
                ShowChatsOnGUI()
                SetAssistantStatus("Answering...")
                await asyncio.to_thread(TextToSpeech, error_response)
                
        except Exception as e:
            print(f"Error executing automation commands: {e}")
            error_response = "Sorry, there was an error executing your request."
            current_chat_log.append({"role": "assistant", "content": error_response})
            SaveChatLogJson(current_chat_log)
            ShowTextToScreen(f"{Assistantname}: {error_response}")
            ChatLogIntegration()
            ShowChatsOnGUI()
            SetAssistantStatus("Answering...")
            await asyncio.to_thread(TextToSpeech, error_response)
    
    # Handle conversational queries
    processed_conversational = False
    
    # Process realtime queries
    realtime_query_part = ""
    for q in general_or_realtime_queries:
        if q.lower().startswith("realtime"):
            realtime_query_part = _extract_parenthesized_query(q.removeprefix("realtime"))
            break

    if realtime_query_part:
        SetAssistantStatus("Searching...")
        print(f"Performing real-time search for: {realtime_query_part}")
        Answer = await asyncio.to_thread(RealTimeSearchEngine, QueryModifier(realtime_query_part))
        print(f"Real-time answer: {Answer}")
        
        current_chat_log.append({"role": "assistant", "content": Answer})
        SaveChatLogJson(current_chat_log)
        ShowTextToScreen(f"{Assistantname}: {Answer}")
        ChatLogIntegration()
        ShowChatsOnGUI()
        SetAssistantStatus("Answering...")
        await asyncio.to_thread(TextToSpeech, Answer)
        processed_conversational = True
        
    # Process general queries (only if no automation was executed)
    if not processed_conversational and not automation_commands_to_execute:
        general_query_part = ""
        for q in general_or_realtime_queries:
            if q.lower().startswith("general"):
                general_query_part = _extract_parenthesized_query(q.removeprefix("general"))
                break

        if general_query_part:
            SetAssistantStatus("Thinking...")
            print(f"Querying ChatBot for: {general_query_part}")
            Answer = await asyncio.to_thread(ChatBot, QueryModifier(general_query_part))
            print(f"ChatBot answer: {Answer}")

            current_chat_log.append({"role": "assistant", "content": Answer})
            SaveChatLogJson(current_chat_log)
            ShowTextToScreen(f"{Assistantname}: {Answer}")
            ChatLogIntegration()
            ShowChatsOnGUI()
            SetAssistantStatus("Answering...")
            await asyncio.to_thread(TextToSpeech, Answer)
            processed_conversational = True

    # Default response if nothing was processed
    if not automation_commands_to_execute and not processed_conversational:
        Answer = "I'm sorry, I couldn't understand that command. Can you please rephrase?"
        current_chat_log.append({"role": "assistant", "content": Answer})
        SaveChatLogJson(current_chat_log)
        ShowTextToScreen(f"{Assistantname}: {Answer}")
        ChatLogIntegration()
        ShowChatsOnGUI()
        SetAssistantStatus("Answering...")
        await asyncio.to_thread(TextToSpeech, Answer)
        print(f"No specific task handled. Default response: {Answer}")
        return False
    
    print("--- process_user_query_async Finished ---")
    return True

def MainExecutionWrapper():
    """Wrapper to be called by the non-GUI thread."""
    global current_chat_log
    
    current_chat_log = ReadChatLogJson()

    SetAssistantStatus("Listening...")
    query = SpeechRecognition()
    
    if query:  # Only process if we got a valid query
        current_chat_log.append({"role": "user", "content": query})
        SaveChatLogJson(current_chat_log)
        ChatLogIntegration()
        ShowChatsOnGUI()

        success = run_async_in_thread(process_user_query_async(query))
        return success
    else:
        print("No query received from speech recognition")
        return False

def FirstThread():
    global background_async_loop
    background_async_loop = asyncio.new_event_loop()
    asyncio.set_event_loop(background_async_loop)
    print("Background async loop started.")
    background_async_loop.run_forever()

if __name__ == "__main__":
    async_thread = threading.Thread(target=FirstThread, daemon=True)
    async_thread.start()

    sleep(0.5)  # Give the async thread a moment to start its event loop
    
    def main_loop_wrapper_for_thread():
        while True:
            try:
                if GetMicrophoneStatus() == "True":
                    MainExecutionWrapper()
                else:
                    if "Available..." not in GetAssistantStatus():
                        SetAssistantStatus("Available...")
            except Exception as e:
                print(f"[ERROR in main_loop_wrapper_for_thread] {e}")
            sleep(0.1)

    main_execution_thread = threading.Thread(target=main_loop_wrapper_for_thread, daemon=True)
    main_execution_thread.start()

    GraphicalUserInterface()
    
    print("GUI closed. Application shutting down.")