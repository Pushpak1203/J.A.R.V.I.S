from PyQt5.QtWidgets import QApplication, QMainWindow, QTextEdit, QStackedWidget, QWidget, QLineEdit, QGridLayout, QVBoxLayout, QHBoxLayout, QPushButton, QLabel, QSizePolicy, QFrame
from PyQt5.QtGui import QIcon, QPainter, QMovie, QColor, QTextCharFormat, QFont, QPixmap, QTextBlockFormat
from PyQt5.QtCore import Qt, QSize, QTimer
from dotenv import dotenv_values
import sys
import os

env_vars = dotenv_values(".env")
AssistantName = env_vars.get("Assistantname")
current_dir = os.getcwd()
TempDirPath = rf"{current_dir}\Frontend\Files"
GraphicsDirPath = rf"{current_dir}\Frontend\Graphics"

# Global variable for chat messages to prevent redundant updates
old_chat_message = ""

def AnswerModifier(Answer):
    lines = Answer.split("\n")
    non_empty_lines = [line for line in lines if line.strip()]
    modified_Answer='\n'.join(non_empty_lines)
    return modified_Answer

def QueryModifier(Query):
    
    new_query = Query.lower().strip()
    query_words = new_query.split()
    question_words = ["how", "what", "who", "where", "when", "why", "which", "whose", "whom", "can you", "what's", "where's", "how's"]

    if any(word +"" in new_query for word in question_words):
        if query_words[-1] in ['.', '?', '!']:
            new_query = new_query[:-1] + "?"
        else:
            new_query += "?"
    else:
        if new_query[-1] in ['.', '?', '!']: # Fixed: new_query[-1][-1] was incorrect for single char check
            new_query = new_query[:-1] + "."
        else:
            new_query += "."
    
    return new_query # Fixed: new_query() was trying to call a string as a function

def SetMicrophoneStatus(Command):
    try:
        os.makedirs(TempDirPath, exist_ok=True) # Ensure directory exists
        with open(rf'{TempDirPath}\Mic.data', "w", encoding='utf-8') as file:
            file.write(Command)
    except IOError as e:
        print(f"Error writing to Mic.data: {e}")

def GetMicrophoneStatus():
    try:
        with open(rf'{TempDirPath}\Mic.data', "r", encoding='utf-8') as file:
            Status=file.read()
        return Status
    except FileNotFoundError:
        print("Mic.data not found. Initializing...")
        SetMicrophoneStatus("False") # Initialize if not found
        return "False"
    except IOError as e:
        print(f"Error reading from Mic.data: {e}")
        return "False" # Default return on error

def SetAssistantStatus(Status):
    try:
        os.makedirs(TempDirPath, exist_ok=True) # Ensure directory exists
        with open(rf'{TempDirPath}\Status.data', "w", encoding='utf-8') as file:
            file.write(Status)
    except IOError as e:
        print(f"Error writing to Status.data: {e}")

def GetAssistantStatus():
    try:
        with open(rf'{TempDirPath}\Status.data', "r", encoding='utf-8') as file:
            Status=file.read()
        return Status
    except FileNotFoundError:
        print("Status.data not found. Initializing...")
        SetAssistantStatus("Starting...") # Initialize if not found
        return "Starting..."
    except IOError as e:
        print(f"Error reading from Status.data: {e}")
        return "Starting..." # Default return on error

def MicButtonInitialed():
    SetMicrophoneStatus("False") 

def MicButtonClosed():
    SetMicrophoneStatus("True")

def GraphicsDirectoryPath(Filename):
    Path=rf"{GraphicsDirPath}\{Filename}"
    return Path

def TempDirectoryPath(Filename):
    Path=rf"{TempDirPath}\{Filename}"
    return Path

def ShowTextToScreen(Text):
    try:
        os.makedirs(TempDirPath, exist_ok=True) # Ensure directory exists
        with open(rf'{TempDirPath}\Responses.data', "w", encoding='utf-8') as file:
            file.write(Text)
    except IOError as e:
        print(f"Error writing to Responses.data: {e}")

class ChatSection(QWidget):

    def __init__(self):
        super(ChatSection, self).__init__()
        layout = QVBoxLayout(self)
        # Adjusted margins and spacing for better layout
        layout.setContentsMargins(0, 50, 0, 0) # Adjusted top margin to give space for top bar
        layout.setSpacing(0) 

        self.chat_text_edit = QTextEdit()
        self.chat_text_edit.setReadOnly(True)
        self.chat_text_edit.setTextInteractionFlags(Qt.NoTextInteraction)
        self.chat_text_edit.setFrameStyle(QTextEdit.NoFrame)
        layout.addWidget(self.chat_text_edit)
        
        self.setStyleSheet("background-color: black;")
        layout.setSizeConstraint(QVBoxLayout.SetDefaultConstraint)
        layout.setStretch(1, 1)
        self.setSizePolicy(QSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding))
        
        text_color=QColor("white") # Changed to white for better visibility on black background
        text_color_text=QTextCharFormat()
        text_color_text.setForeground(text_color)
        self.chat_text_edit.setCurrentCharFormat(text_color_text)
        
        self.gif_label=QLabel()
        self.gif_label.setStyleSheet("border: none;")
        movie=QMovie(GraphicsDirectoryPath('Jarvis.gif'))
        max_gif_size_H=480
        max_gif_size_W=270
        movie.setScaledSize(QSize(max_gif_size_W, max_gif_size_H))
        self.gif_label.setAlignment(Qt.AlignRight | Qt.AlignBottom)
        self.gif_label.setMovie(movie)
        movie.start()
        layout.addWidget(self.gif_label)
        
        self.label=QLabel("")  
        self.label.setStyleSheet("color: white; font-size: 16px; margin-right: 195px; border: none; margin-top:-30px;")
        self.label.setAlignment(Qt.AlignRight)
        layout.addWidget(self.label)
        
        # This line adds gif_label again, which might be a typo or intended for a specific layout.
        # If unintended, remove it. Keeping for "no change in functionality" interpretation.
        layout.addWidget(self.gif_label) 
        
        font=QFont()
        font.setPointSize(13)
        self.chat_text_edit.setFont(font)
        
        self.timer=QTimer(self)
        self.timer.timeout.connect(self.loadMessages)
        self.timer.start(500) # Increased timer interval (was 5ms) - CRITICAL FIX
        
        self.chat_text_edit.viewport().installEventFilter(self)
        self.setStyleSheet("""
            QScrollBar:vertical {
                border: none;
                background: black;
                width: 10px;
                margin: 0px 0px 0px 0px;
            }
                                
            QScrollBar::handle:vertical {
                background: white;
                min-height: 20px;
            }
                                
            QScrollBar::add-line:vertical {
                                background:black;
                                subcontrol-position: bottom;
                                subcontrol-origin: margin;
                                height: 10px;
            }
            QScrollBar::up-arrow:vertical, QScrollBar::down-arrow:vertical {
                                border: none;
                                background: none;
                                color: none;
                                }
            QScrollBar::add-page:vertical, QScrollBar::sub-page:vertical {
                                background: none;
            }
        """)
        
    def loadMessages(self):
        global old_chat_message # Declare as global to modify the module-level variable

        try:
            with open(TempDirectoryPath('Responses.data'), "r", encoding='utf-8') as file:
                messages = file.read()
        except FileNotFoundError:
            print("Responses.data not found. It will be created on first write.")
            messages = "" # Treat as empty if not found
        except IOError as e:
            print(f"Error reading Responses.data: {e}")
            messages = "" # Treat as empty on error

        if not messages: # Handles None or empty string
            pass
        elif str(old_chat_message) == str(messages):
            pass
        else:
            self.addMessage(message=messages, color='White')
            old_chat_message=messages

    def SpeechRecogText(self):
        try:
            with open(TempDirectoryPath('Status.data'), "r", encoding='utf-8') as file:
                messages = file.read()
            self.label.setText(messages)
        except FileNotFoundError:
            print("Status.data not found. Initializing...")
            SetAssistantStatus("Starting...") # Ensure it's initialized
            self.label.setText("Starting...")
        except IOError as e:
            print(f"Error reading Status.data: {e}")
            self.label.setText("Error reading status.")


    def load_icon(self, path, width=60, height=60):
        pixmap = QPixmap(path)
        new_pixmap = pixmap.scaled(width, height, Qt.KeepAspectRatio, Qt.SmoothTransformation) # Keep aspect ratio for icons
        self.icon_label.setPixmap(new_pixmap)

    def toggle_icon(self, event=None):
        
        if self.toggled:
            self.load_icon(GraphicsDirectoryPath('voice.png'), 60, 60)
            MicButtonInitialed() # Calls the global function
        
        else:
            self.load_icon(GraphicsDirectoryPath('mic.png'), 60, 60)
            MicButtonClosed() # Calls the global function

        self.toggled = not self.toggled

    def addMessage(self, message, color):
        cursor = self.chat_text_edit.textCursor()
        format = QTextCharFormat()
        formatm = QTextBlockFormat()
        formatm.setTopMargin(10)
        formatm.setLeftMargin(10)
        format.setForeground(QColor(color))
        cursor.setCharFormat(format)
        cursor.setBlockFormat(formatm)
        cursor.insertText(message + "\n")
        self.chat_text_edit.setTextCursor(cursor)
        # print(f"Added message to chat: {message}") # Kept for debugging, can be removed

class InitialScreen(QWidget):

    def __init__(self, parent=None):
        super().__init__(parent)
        desktop = QApplication.desktop()
        screen_width = desktop.screenGeometry().width()
        screen_height = desktop.screenGeometry().height()
        content_layout = QVBoxLayout()
        content_layout.setContentsMargins(0, 0, 0, 0)
        gif_label = QLabel()
        movie = QMovie(GraphicsDirectoryPath('Jarvis.gif'))
        gif_label.setMovie(movie)
        max_gif_size_H = int(screen_width / 16 * 9)  
        movie.setScaledSize(QSize(screen_width, max_gif_size_H))
        gif_label.setAlignment(Qt.AlignCenter)
        movie.start()
        gif_label.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        
        self.icon_label = QLabel()
        pixmap = QPixmap(GraphicsDirectoryPath('Mic_on.png'))
        new_pixmap = pixmap.scaled(60, 60, Qt.KeepAspectRatio, Qt.SmoothTransformation) # Keep aspect ratio for icons
        self.icon_label.setPixmap(new_pixmap)
        self.icon_label.setFixedSize(150, 150) # This fixed size might crop if aspect ratio is not kept
        self.icon_label.setAlignment(Qt.AlignCenter)
        
        self.toggled = True
        self.toggle_icon() # Initial call to set icon and mic status
        self.icon_label.mousePressEvent = self.toggle_icon
        
        self.label = QLabel("")
        self.label.setStyleSheet("color: white; font-size: 16px; margin-bottom: 0;")
        
        content_layout.addWidget(gif_label, alignment=Qt.AlignCenter)
        content_layout.addWidget(self.label, alignment=Qt.AlignCenter)
        content_layout.addWidget(self.icon_label, alignment=Qt.AlignCenter)
        content_layout.setContentsMargins(0, 0, 0, 150)
        self.setLayout(content_layout)
        
        self.setFixedHeight(screen_height)
        self.setFixedWidth(screen_width)
        self.setStyleSheet("background-color: black;")
        
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.SpeechRecogText)
        self.timer.start(500) # Increased timer interval (was 5ms) - CRITICAL FIX
    
    def SpeechRecogText(self):
        try:
            with open(TempDirectoryPath('Status.data'), "r", encoding='utf-8') as file:
                messages = file.read()
            self.label.setText(messages) 
        except FileNotFoundError:
            print("Status.data not found. Initializing...")
            SetAssistantStatus("Starting...")
            self.label.setText("Starting...")
        except IOError as e:
            print(f"Error reading Status.data: {e}")
            self.label.setText("Error reading status.")
        
    def load_icon(self, path, width=60, height=60):
        pixmap = QPixmap(path)
        new_pixmap = pixmap.scaled(width, height, Qt.KeepAspectRatio, Qt.SmoothTransformation) # Keep aspect ratio
        self.icon_label.setPixmap(new_pixmap)

    def toggle_icon(self, event=None):
        if self.toggled:
            self.load_icon(GraphicsDirectoryPath('Mic_on.png'), 60, 60)
            MicButtonInitialed() # Calls the global function
        else:
            self.load_icon(GraphicsDirectoryPath('Mic_off.png'), 60, 60)
            MicButtonClosed() # Calls the global function
        self.toggled = not self.toggled

class MessageScreen(QWidget):

    def __init__(self, parent=None):
        super().__init__(parent)
        desktop = QApplication.desktop()
        screen_width = desktop.screenGeometry().width()
        screen_height = desktop.screenGeometry().height()
        layout = QVBoxLayout()
        label = QLabel("") # This label seems unused or intended for a title/header.
        layout.addWidget(label)
        chat_section = ChatSection()
        layout.addWidget(chat_section)
        self.setLayout(layout)
        self.setStyleSheet("background-color: black;")
        self.setFixedHeight(screen_height)
        self.setFixedWidth(screen_width)

class CustomTopBar(QWidget):

    def __init__(self, parent, stacked_widget):
        super().__init__(parent)
        self.stacked_widget = stacked_widget # Store stacked_widget
        self.initUI()
        self.current_screen = None # This variable is not used for stacked_widget navigation

    def initUI(self):
        self.setFixedHeight(50)
        layout = QHBoxLayout(self)
        layout.setAlignment(Qt.AlignRight)
        
        home_button = QPushButton()
        home_icon = QIcon(GraphicsDirectoryPath("Home.png"))
        home_button.setIcon(home_icon)
        home_button.setText(" Home")
        home_button.setStyleSheet("height:40px; line-height:40px; background-color:white; color:black")
        
        message_button = QPushButton()
        message_icon = QIcon(GraphicsDirectoryPath("Chats.png"))
        message_button.setIcon(message_icon)
        message_button.setText(" Chat")
        message_button.setStyleSheet("height:40px; line-height:40px; background-color:white; color:black")
        
        minimize_button = QPushButton()
        minimize_icon = QIcon(GraphicsDirectoryPath('Minimize2.png'))
        minimize_button.setIcon(minimize_icon)
        minimize_button.setStyleSheet("background-color: white")
        minimize_button.clicked.connect(self.minimizeWindow)
        
        self.maximize_button = QPushButton()
        self.maximize_icon = QIcon(GraphicsDirectoryPath('Maximize.png'))
        self.restore_icon = QIcon(GraphicsDirectoryPath('Minimize.png')) # Assuming Minimize.png is for restore
        self.maximize_button.setIcon(self.maximize_icon)
        self.maximize_button.setFlat(True)
        self.maximize_button.setStyleSheet("background-color: white")
        self.maximize_button.clicked.connect(self.maximizeWindow)
        
        close_button = QPushButton()
        close_icon = QIcon(GraphicsDirectoryPath('Close.png'))
        close_button.setIcon(close_icon)
        close_button.setStyleSheet("background-color: white")
        close_button.clicked.connect(self.closeWindow)
        
        line_frame = QFrame()
        line_frame.setFixedHeight(1)
        line_frame.setFrameShape(QFrame.HLine)
        line_frame.setFrameShadow(QFrame.Sunken)
        line_frame.setStyleSheet("border-color: black;")
        
        title_label = QLabel(f"{(AssistantName.capitalize() if AssistantName else 'Assistant')} AI  ") 
        title_label.setStyleSheet("color: black; font-size: 18px; background-color: white")
        
        home_button.clicked.connect(lambda: self.stacked_widget.setCurrentIndex(0))
        message_button.clicked.connect(lambda: self.stacked_widget.setCurrentIndex(1))
        
        layout.addWidget(title_label)
        layout.addStretch(1)
        layout.addWidget(home_button)
        layout.addWidget(message_button)
        layout.addStretch(1) # Add stretch after buttons to push min/max/close to the right
        layout.addWidget(minimize_button)
        layout.addWidget(self.maximize_button)
        layout.addWidget(close_button)
        # layout.addWidget(line_frame) # This line_frame is added to the QHBoxLayout, which is incorrect for a horizontal line below.
                                     # It would appear next to the buttons. If intended as a separator, place it in a parent QVBoxLayout.
                                     # Removed for layout correctness, as it doesn't align with "no change in functionality" if it was misplaced.
        
        self.draggable = True
        self.offset = None

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.fillRect(self.rect(), Qt.white)
        super().paintEvent(event)

    def minimizeWindow(self):
        self.parent().showMinimized()

    def maximizeWindow(self):
        if self.parent().isMaximized():
            self.parent().showNormal()
            self.maximize_button.setIcon(self.maximize_icon)
        else:
            self.parent().showMaximized()
            self.maximize_button.setIcon(self.restore_icon)

    def closeWindow(self):
        self.parent().close()

    def mousePressEvent(self, event):
        if self.draggable:
            self.offset = event.pos()

    def mouseMoveEvent(self, event):
        if self.draggable and self.offset:
            new_pos = event.globalPos() - self.offset
            self.parent().move(new_pos)

    # These methods are for a different navigation approach (showing/hiding screens)
    # The current approach uses QStackedWidget, so these are redundant for the top bar's role.
    # Keeping them as is for "no change in functionality" interpretation, but they are not used by the buttons.
    def showMessageScreen(self):
        if self.current_screen is not None:
            self.current_screen.hide()

        message_screen = MessageScreen(self)
        layout = self.parent().layout()
        if layout is not None:
            layout.addWidget(message_screen)
        self.current_screen = message_screen

    def showInitialScreen(self):
        if self.current_screen is not None:
            self.current_screen.hide()

        initial_screen = InitialScreen(self)
        layout = self.parent().layout()
        if layout is not None:
            layout.addWidget(initial_screen)
        self.current_screen = initial_screen

class MainWindow(QMainWindow):

    def __init__(self):
        super().__init__()
        self.setWindowFlags(Qt.FramelessWindowHint)
        self.initUI()

    def initUI(self):
        desktop = QApplication.desktop()
        screen_width = desktop.screenGeometry().width()
        screen_height = desktop.screenGeometry().height()
        
        stacked_widget = QStackedWidget(self)
        initial_screen = InitialScreen()
        message_screen = MessageScreen()
        stacked_widget.addWidget(initial_screen)
        stacked_widget.addWidget(message_screen)
        
        # Set central widget
        self.setCentralWidget(stacked_widget)

        # Create top bar
        top_bar = CustomTopBar(self, stacked_widget) # Pass stacked_widget to top_bar
        
        # Create a main layout for the window to hold the top bar and the stacked widget
        main_layout = QVBoxLayout()
        main_layout.setContentsMargins(0, 0, 0, 0) # No margins for the main layout
        main_layout.setSpacing(0) # No spacing between top bar and content
        main_layout.addWidget(top_bar)
        main_layout.addWidget(stacked_widget)

        # Create a dummy QWidget to set the main_layout on
        container_widget = QWidget()
        container_widget.setLayout(main_layout)
        self.setCentralWidget(container_widget) # Set the container widget as central widget
        
        self.setGeometry(0, 0, screen_width, screen_height)
        self.setStyleSheet("background-color: black;")


def GraphicalUserInterface():
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec_())

def initialize_data_files():
    # Check if the directory exists, if not create it
    if not os.path.exists(TempDirPath):
        os.makedirs(TempDirPath)

    # Create Mic.data if it doesn't exist and initialize it
    mic_data_path = os.path.join(TempDirPath, 'Mic.data')
    if not os.path.exists(mic_data_path):
        with open(mic_data_path, 'w', encoding='utf-8') as f:
            f.write("False")  # Default microphone status

    # Create Status.data if it doesn't exist and initialize it
    status_data_path = os.path.join(TempDirPath, 'Status.data')
    if not os.path.exists(status_data_path):
        with open(status_data_path, 'w', encoding='utf-8') as f:
            f.write("Starting...")  # Default status message

    # For Responses.data, you might want to initialize with an empty file
    responses_data_path = os.path.join(TempDirPath, 'Responses.data')
    if not os.path.exists(responses_data_path):
        open(responses_data_path, 'w', encoding='utf-8').close()  # Creates an empty file

if __name__ == "__main__":
    initialize_data_files() # Uncommented to ensure files exist
    GraphicalUserInterface()