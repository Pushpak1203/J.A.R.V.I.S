# 🤖 J.A.R.V.I.S – AI-Powered Personal Assistant

[![Build Status](https://img.shields.io/badge/build-passing-brightgreen)]()
[![License](https://img.shields.io/badge/license-MIT-blue.svg)]()
[![Python](https://img.shields.io/badge/python-3.10+-blue.svg)]()
[![Platform](https://img.shields.io/badge/platform-Windows-lightgrey)]()

J.A.R.V.I.S (Just A Rather Very Intelligent System) is a Python-based smart assistant inspired by Tony Stark’s iconic AI. It listens, understands, responds, and takes action — combining real-time search capabilities with seamless system automation using natural language voice commands.

---

## 🚀 Features

- 🔊 **Voice Command Recognition**  
- 🧠 **Intent Classification via LLM (Cohere)**
- 🌐 **Real-Time Search Engine Integration**
- 🖥️ **System Automation** (open apps, control volume, play media, etc.)
- 🗣️ **Conversational Interaction**
- 🖼️ **(WIP)** Image generation using Hugging Face Stable Diffusion

---

## 🧰 Tech Stack

- **Python** – Core programming language
- **Cohere** – LLM-powered intent classification
- **Selenium** – Web automation
- **AppOpener** – App launching (Windows support)
- **PyQt5** – GUI (optional frontend interface)
- **Edge-TTS / Pyttsx3** – Voice synthesis
- **SpeechRecognition + Pyaudio** – Voice input
- **HuggingFace API** – Image generation via Stable Diffusion

---

## 🎯 How It Works

1. User speaks or types a query  
2. The system classifies intent using Cohere LLM  
3. Based on intent:
   - General queries → passed to chatbot
   - Real-time info → fetched via web scraping or APIs
   - Automation → system-level commands are triggered  
4. Response is spoken out via TTS and displayed

---

## 📂 Project Structure

```
JARVIS/
├── Backend/
│   ├── Main.py              # Main orchestration script
│   ├── Model.py             # Query classifier using Cohere
│   ├── ChatBot.py           # Handles general queries
│   ├── RealTimeSearchEngine.py  # For fetching real-time data
│   ├── Automation.py        # System-level command execution
│   └── ImageGeneration.py   # (Optional) Image generation logic
├── Frontend/
│   ├── GUI.py               # PyQt5-based interface (optional)
│   └── Files/
│       └── ImageGeneration.data
├── Data/
│   ├── ChatLog.json         # Conversation log
│   └── Generated images
├── .env                     # Stores API keys
├── requirements.txt         # All Python dependencies
└── README.md
```

---

## ⚙️ Installation

1. **Clone the repository**
```bash
git clone https://github.com/your-username/JARVIS.git
cd JARVIS
```

2. **Create and activate a virtual environment**
```bash
python -m venv venv
venv\Scripts\activate   # On Windows
```

3. **Install dependencies**
```bash
pip install -r requirements.txt
```

4. **Add your environment variables to `.env`**
```
CohereAPIKey=your_cohere_api_key
HuggingFaceAPIKey=your_huggingface_api_key
Username=YourName
Assistantname=J.A.R.V.I.S
```

---

## ▶️ Run the Assistant

To start the assistant in CLI mode:

```bash
python Backend/Main.py
```

For image generation to run in the background:

```bash
python Backend/ImageGeneration.py
```

---

## ✅ Status

- ✅ Real-time query classification
- ✅ System command execution
- ✅ Conversational chatbot
- ✅ Real-time search integration
- 🟡 Image generation (in progress)
- 🟡 GUI interface (optional and expanding)

---

## 💡 Inspiration

This project is inspired by **Tony Stark’s J.A.R.V.I.S** from the Marvel Universe — reimagined using modern AI tools like LLMs, voice interfaces, and system automation.

---

## 📬 Feedback & Collaboration

This is a passion project aimed at pushing the limits of intelligent assistants.  
Feel free to fork, star ⭐, raise issues, or reach out for collaborations.

---

## 📜 License

[MIT License](LICENSE)

---

### 🧠 “I am not just a voice in your head. I’m the system behind your superpowers.”  
— J.A.R.V.I.S, Reimagined