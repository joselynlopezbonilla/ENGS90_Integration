from curses.ascii import EM
import sys
import time
from PyQt5.QtWidgets import QApplication, QWidget, QLabel, QPushButton, QToolButton, QMainWindow, QSplashScreen, QFrame, QTableWidget, QHeaderView,  QTableWidgetItem, QVBoxLayout, QHeaderView 
#from PyQt5.QtGui import QIcon, QPixmap, QColor, QPalette
from PyQt5 import QtGui
from PyQt5.QtCore import Qt, pyqtSignal
from Status import Status
import threading
import gpiod
#import seek

chip1=gpiod.Chip('gpiochip1')
chip4=gpiod.Chip('gpiochip4')

LED_line=chip1.get_lines([ 7 ]) # Pin 21
button1_line=chip1.get_lines([ 9 ]) # Pin 23
button2_line=chip1.get_lines([ 21 ]) # Pin 5
button3_line=chip4.get_lines([ 24 ]) # Pin 7
button4_line=chip1.get_lines([ 8 ]) # Pin 19
button5_line=chip1.get_lines([ 11 ]) # Pin 27
button6_line=chip4.get_lines([ 27 ]) # Pin 29
button7_line=chip4.get_lines([ 28 ]) # Pin 31

LED_line.request(consumer='foobar', type=gpiod.LINE_REQ_DIR_OUT, default_vals=[ 0 ])
button1_line.request(consumer='button1', type=gpiod.LINE_REQ_DIR_IN)
button2_line.request(consumer='button2', type=gpiod.LINE_REQ_DIR_IN)
button3_line.request(consumer='button3', type=gpiod.LINE_REQ_DIR_IN)
button4_line.request(consumer='button4', type=gpiod.LINE_REQ_DIR_IN)
button5_line.request(consumer='button5', type=gpiod.LINE_REQ_DIR_IN)
button6_line.request(consumer='button6', type=gpiod.LINE_REQ_DIR_IN)
button7_line.request(consumer='button7', type=gpiod.LINE_REQ_DIR_IN)

APPLICATION = None
ROLLING_STATUS = button1_line.get_values()[0]
ORIENT_STATUS = button2_line.get_values()[0]
PLACING_STATUS = button3_line.get_values()[0]
FULL_STATUS = button4_line.get_values()[0]
EMERGENCY_STATUS = button5_line.get_values()[0]
PART_STATUS = button6_line.get_values()[0]
SPLITTER_STATUS = button7_line.get_values()[0]


# APPLICATION = None
# ROLLING_STATUS = 0
# ORIENT_STATUS = 0
# PLACING_STATUS = 0
# FULL_STATUS = 0
# PART_STATUS = 0
# EMERGENCY_STATUS = 0
curr_status = Status.READY

# Background function to poll signal changes from the machine
def background():
    global ROLLING_STATUS, ORIENT_STATUS, PLACING_STATUS, FULL_STATUS, EMERGENCY_STATUS, PART_STATUS, SPLITTER_STATUS
    prev_rolling = ROLLING_STATUS
    prev_orient = ORIENT_STATUS
    prev_placing = PLACING_STATUS
    prev_full = FULL_STATUS
    prev_emergency = EMERGENCY_STATUS
    prev_part = PART_STATUS
    prev_splitter = SPLITTER_STATUS

    while True:
        ROLLING_STATUS = button1_line.get_values()[0]
        ORIENT_STATUS = button2_line.get_values()[0]
        PLACING_STATUS = button3_line.get_values()[0]
        FULL_STATUS = button4_line.get_values()[0]
        EMERGENCY_STATUS = button5_line.get_values()[0]
        PART_STATUS = button6_line.get_values()[0]
        SPLITTER_STATUS = button7_line.get_values()[0]
        
        # Comparing previous signal values with current signal values
        if prev_rolling != ROLLING_STATUS:
            if ROLLING_STATUS == 1:
                APPLICATION.ROLL_ERROR = ROLLING_STATUS
            prev_rolling = ROLLING_STATUS
        elif prev_orient != ORIENT_STATUS:
            if ORIENT_STATUS == 1:
                APPLICATION.ORIENT_ERROR = ORIENT_STATUS
            prev_orient = ORIENT_STATUS        
        elif prev_placing != PLACING_STATUS:
            if PLACING_STATUS == 1:
                APPLICATION.PLACING_ERROR = PLACING_STATUS
            prev_placing = PLACING_STATUS
        elif prev_full != FULL_STATUS:
            if FULL_STATUS == 1:
                APPLICATION.FULL_SCREEN = FULL_STATUS
            prev_full = FULL_STATUS
        elif prev_emergency != EMERGENCY_STATUS:
            if EMERGENCY_STATUS == 1:
                APPLICATION.EMERGENCY_SCREEN = EMERGENCY_STATUS
            prev_emergency = EMERGENCY_STATUS
        elif prev_part != PART_STATUS:
            if PART_STATUS == 1:
                APPLICATION.PART_ERROR = PART_STATUS
            prev_part = PART_STATUS
        elif prev_splitter != SPLITTER_STATUS:
            if SPLITTER_STATUS == 1:
                APPLICATION.SPLITTER_ERROR = SPLITTER_STATUS
            prev_splitter = SPLITTER_STATUS
        time.sleep(.1)

# Will begin running the entire HMI application
def run_app():
    global APPLICATION
    app = QApplication(sys.argv)
    splash = SplashScreen()
    time.sleep(1) # fake ready signal after 1 secs
    APPLICATION = ReorientationApp()
    APPLICATION.show()
    splash.finish(APPLICATION)
    app.exec()

class ReorientationApp(QMainWindow):
    rolling_signal = pyqtSignal(str, int)
    ROLL = "ROLL"

    orienting_signal = pyqtSignal(str, int)
    ORIENT = "ORIENT"

    placing_signal = pyqtSignal(str, int)
    PLACING = "PLACING"

    full_signal = pyqtSignal(str, int)
    FULL = "FULL"

    emergency_signal = pyqtSignal(str, int)
    EMERGENCY = "EMERGENCY"

    part_signal = pyqtSignal(str, int)
    PART = "PART"

    splitter_signal = pyqtSignal(str, int)
    SPLITTER = "SPLITTER"

    def __init__(self):
        super(ReorientationApp, self).__init__()
        widget = MainPage(self.changeWidget)
        widget.setStyleSheet(" background-color: rgb(0, 110, 0);")
        self.rolling_signal.connect(self.handleRMSignal)
        self.orienting_signal.connect(self.handleOMSignal)
        self.placing_signal.connect(self.handlePMSignal)
        self.full_signal.connect(self.handleFMSignal)
        self.emergency_signal.connect(self.handleEMSignal)
        self.part_signal.connect(self.handlePartMSignal)
        self.splitter_signal.connect(self.handlePartSMSignal)

        self.setCentralWidget(widget)
        self.showFullScreen()
        self.setWindowTitle("Reorientation Machine")

    def changeWidget(self, widget):
        self.setCentralWidget(widget)

    @property
    def ROLL_ERROR(self):
        return self._ROLLING_STATUS

    @ROLL_ERROR.setter
    def ROLL_ERROR(self, value):
        self._ROLLING_STATUS = value
        print("setting and emitting")
        self.rolling_signal.emit(self.ROLL, self._ROLLING_STATUS)

    def handleRMSignal(self, name, value):
        self.displayRollingError(value)

    @property
    def ORIENT_ERROR(self):
        return self._ORIENT_STATUS

    @ORIENT_ERROR.setter
    def ORIENT_ERROR(self, value):
        self._ORIENT_STATUS = value
        print("setting and emitting")
        self.orienting_signal.emit(self.ORIENT, self._ORIENT_STATUS)

    def handleOMSignal(self, name, value):
        self.displayOrientError(value)

    @property
    def PLACING_ERROR(self):
        return self._PLACING_STATUS

    @PLACING_ERROR.setter
    def PLACING_ERROR(self, value):
        self._PLACING_STATUS = value
        print("setting and emitting")
        self.placing_signal.emit(self.PLACING, self._PLACING_STATUS)

    def handlePMSignal(self, name, value):
        self.displayPlacingError(value)

    @property
    def FULL_SCREEN(self):
        return self._FULL_STATUS

    @FULL_SCREEN.setter
    def FULL_SCREEN(self, value):
        self._FULL_STATUS = value
        print("setting and emitting")
        self.full_signal.emit(self.FULL, self._FULL_STATUS)

    def handleFMSignal(self, name, value):
        self.displayFullTray(value)

    @property
    def EMERGENCY_SCREEN(self):
        return self._EMERGENCY_STATUS

    @EMERGENCY_SCREEN.setter
    def EMERGENCY_SCREEN(self, value):
        self._EMERGENCY_STATUS = value
        print("setting and emitting")
        self.emergency_signal.emit(self.EMERGENCY, self._EMERGENCY_STATUS)

    def handleEMSignal(self, name, value):
        self.displayEmergency(value)

    @property
    def PART_ERROR(self):
        return self._PART_STATUS

    @PART_ERROR.setter
    def PART_ERROR(self, value):
        self._PART_STATUS = value
        print("setting and emitting")
        self.part_signal.emit(self.PART, self._PART_STATUS)

    def handlePartMSignal(self, name, value):
        self.displayPartError(value)

    @property
    def SPLITTER_ERROR(self):
        return self._SPLITTER_STATUS

    @SPLITTER_ERROR.setter
    def SPLITTER_ERROR(self, value):
        self._SPLITTER_STATUS = value
        print("setting and emitting")
        self.splitter_signal.emit(self.SPLITTER, self._SPLITTER_STATUS)

    def handlePartSMSignal(self, name, value):
        self.displaySplitterError(value)

    def displayRollingError(self, signal):
        widget = RollingDisplay(self.changeWidget)
        widget.setStyleSheet(" background-color: rgb(171, 0, 0);")
        self.setCentralWidget(widget)

    def displayOrientError(self, signal):
        widget = InterlockDisplay(self.changeWidget)
        self.setCentralWidget(widget)
        widget.setStyleSheet("background-color: rgb(171, 0, 0);")

    def displayFullTray(self, signal):
        widget = FullDisplay(self.changeWidget)
        self.setCentralWidget(widget)
        widget.setStyleSheet("background-color: rgb(0, 0, 148);") 

    def displayPlacingError(self, signal):
        #Aruco marker cannot be found properly
        widget = PlacingDisplay(self.changeWidget)
        self.setCentralWidget(widget)
        widget.setStyleSheet("background-color: rgb(171, 0, 0);")

    def displayEmergency(self, signal):
        # Total printer failure or pnp failure vertical axis
        widget = EmerStopDisplay(self.changeWidget)
        self.setCentralWidget(widget)
        widget.setStyleSheet(" background-color: rgb(171, 0, 0);")

    def displayPartError(self, signal):
        # Detection warning
        # No part detected
        widget = ChamferPartDisplay(self.changeWidget)
        self.setCentralWidget(widget)
        widget.setStyleSheet("background-color: rgb(171, 0, 0);")

    def displaySplitterError(self, signal):
        # No ball seat detected after the splitter
        widget = SplitterDisplay(self.changeWidget)
        self.setCentralWidget(widget)
        widget.setStyleSheet("background-color: rgb(171, 0, 0);")

class SplashScreen():
    def __init__(self):
        # super(SplashScreen,self).__init__()
        pixmap = QtGui.QPixmap("./rob.jpg")
        self.splash = QSplashScreen(pixmap)
        self.splash.show()

    def finish(self, window):
        self.splash.finish(window)


class MainPage(QFrame):
    def __init__(self, callback):
        super(MainPage,self).__init__()
        self.callback = callback
        widget = QWidget(self)
        textLabel = QLabel(widget)
        textLabel.setText("Start Up Completed")
        textLabel.move(170,150)
        font = textLabel.font()
        font.setPointSize(50)
        textLabel.setFont(font)
        textLabel.adjustSize() #seems like a bad idea
        widget.setStyleSheet("color: rgb(255, 255, 255);")
        print(repr(Status.READY))
        
        #self.button1 = QPushButton(self)
        self.button1 = QPushButton("Chamfer Up", self)
        #self.button1.setText("Chamfer Side-Up")
        self.button1.move(100,300)
        self.button1.resize(100, 300)
        self.button1.setStyleSheet(" background-color: rgb(171, 171, 171); \
        border-style: outset; \
        border-width: 2px;\
        border-radius: 10px; \
        border-color: beige; \
        font: bold 30px; \
        min-width: 10em; \
        padding: 6px;")
        self.button1.clicked.connect(self.button1_clicked)

        self.button2 = QPushButton(self)
        self.button2.setText("Chamfer Down")
        self.button2.move(550,300)
        self.button2.resize(100, 300)
        self.button2.setStyleSheet(" background-color: rgb(171, 171, 171); \
        border-style: outset; \
        border-width: 2px;\
        border-radius: 10px; \
        border-color: beige; \
        font: bold 30px; \
        min-width: 10em; \
        padding: 6px;")
        self.button2.clicked.connect(self.button2_clicked)

        self.button3 = QPushButton(self)
        self.button3.setText("Signal Statuses")
        self.button3.move(600,650)
        self.button3.resize(100, 100)
        self.button3.setStyleSheet(" background-color: rgb(171, 171, 171); \
        border-style: outset; \
        border-width: 2px;\
        border-radius: 10px; \
        border-color: beige; \
        font: bold 30px; \
        min-width: 10em; \
        padding: 6px;")
        self.button3.clicked.connect(self.button3_clicked)

    def button1_clicked(self):
        widget = ErrorDisplay(self.callback)
        self.callback(widget)
        widget.setStyleSheet(" background-color: rgb(0, 110, 0);")
        print("Button 1 clicked")
        chamfer = 1 # Chamfer side up
        print(repr(Status.SET))
        curr_status = Status.SET

    def button2_clicked(self):
        widget = ErrorDisplay(self.callback)
        self.callback(widget)
        widget.setStyleSheet(" background-color: rgb(0, 110, 0);")
        print("Button 2 clicked")
        chamfer = 2 # Chamfer side down
        print(repr(Status.SET))
        curr_status = Status.SET

    def button3_clicked(self):
        widget = SignalsDisplay(self.callback)
        self.callback(widget)
        widget.setStyleSheet(" background-color: rgb(0, 110, 0);")
        print("Button 3 clicked")

# Using Keyboard strokes to represent signals coming from the machine
class ErrorDisplay(QFrame):
    def __init__(self, callback):
        super(ErrorDisplay,self).__init__()
        self.callback = callback
        widget = QWidget(self)
        textLabel = QLabel(widget)
        textLabel.setText("Machine in use")
        textLabel.move(150,150)
        font = textLabel.font()
        font.setPointSize(70)
        textLabel.setFont(font) 
        textLabel.adjustSize()
        widget.setStyleSheet("color: rgb(250, 250, 250);")
        print(repr(Status.IN_USE))

        self.button1 = QPushButton(self)
        self.button1.setText("Pause")
        self.button1.move(300,300)
        self.button1.resize(100, 300)
        self.button1.setStyleSheet(" background-color: rgb(171, 171, 171); \
        border-style: outset; \
        border-width: 2px;\
        border-radius: 10px; \
        border-color: beige; \
        font: bold 30px; \
        min-width: 10em; \
        padding: 6px;")
        self.button1.clicked.connect(self.button1_clicked)
        
        self.button3 = QPushButton(self)
        self.button3.setText("Signal Statuses")
        self.button3.move(600,650)
        self.button3.resize(100, 100)
        self.button3.setStyleSheet(" background-color: rgb(171, 171, 171); \
        border-style: outset; \
        border-width: 2px;\
        border-radius: 10px; \
        border-color: beige; \
        font: bold 30px; \
        min-width: 10em; \
        padding: 6px;")
        self.button3.clicked.connect(self.button3_clicked)

    def button1_clicked(self):
        widget = PauseDisplay(self.callback)
        #print(repr(Status.FIXED))
        widget.setStyleSheet(" background-color: rgb(171, 94, 0);")
        self.callback(widget)

    def button3_clicked(self):
        widget = SignalsDisplay(self.callback)
        self.callback(widget)
        widget.setStyleSheet(" background-color: rgb(0, 110, 0);")
        print("Button 3 clicked")

class RollingDisplay(QFrame):
    def __init__(self, callback):
        super(RollingDisplay,self).__init__()
        self.callback = callback
        widget = QWidget(self)
        textLabel = QLabel(widget)
        textLabel.setText("Error: No ball seat presented to the")
        textLabel.move(64,70) 
        font = textLabel.font()
        font.setPointSize(35)
        textLabel.setFont(font)
        textLabel.adjustSize()
        widget.setStyleSheet("color: rgb(250, 250, 250);")

        textLabel1 = QLabel(widget)
        textLabel1.setText("vision system.")
        textLabel1.move(64,135) 
        font = textLabel1.font()
        font.setPointSize(35)
        textLabel1.setFont(font)
        textLabel1.adjustSize()

        textLabel2 = QLabel(widget)
        textLabel2.setText("Check the following:")
        textLabel2.move(64,200) 
        font = textLabel2.font()
        font.setPointSize(35)
        textLabel2.setFont(font)
        textLabel2.adjustSize()
        
        textLabel3 = QLabel(widget)
        textLabel3.setText("1) Rolling filter is not stuck")
        textLabel3.move(64,265) 
        font = textLabel3.font()
        font.setPointSize(35)
        textLabel3.setFont(font)
        textLabel3.adjustSize()
        print(repr(Status.IVALID_PART))

        self.button1 = QPushButton(self)
        self.button1.setText("Clear error")
        self.button1.move(100,330)
        self.button1.resize(100, 300)
        self.button1.setStyleSheet(" background-color: rgb(171, 171, 171); \
        border-style: outset; \
        border-width: 2px;\
        border-radius: 10px; \
        border-color: beige; \
        font: bold 30px; \
        min-width: 10em; \
        padding: 6px;")
        self.button1.clicked.connect(self.button1_clicked)

        self.button2 = QPushButton(self)
        self.button2.setText("Abort")
        self.button2.move(550,330)
        self.button2.resize(100, 300)
        self.button2.setStyleSheet(" background-color: rgb(171, 171, 171); \
        border-style: outset; \
        border-width: 2px;\
        border-radius: 10px; \
        border-color: beige; \
        font: bold 30px; \
        min-width: 10em; \
        padding: 6px;")
        self.button2.clicked.connect(self.button2_clicked)

        self.button3 = QPushButton(self)
        self.button3.setText("Signal Statuses")
        self.button3.move(600,650)
        self.button3.resize(100, 100)
        self.button3.setStyleSheet(" background-color: rgb(171, 171, 171); \
        border-style: outset; \
        border-width: 2px;\
        border-radius: 10px; \
        border-color: beige; \
        font: bold 30px; \
        min-width: 10em; \
        padding: 6px;")
        self.button3.clicked.connect(self.button3_clicked)

    def button1_clicked(self):
        widget = ErrorDisplay(self.callback)
        print(repr(Status.FIXED))
        widget.setStyleSheet(" background-color: rgb(0, 110, 0);")
        self.callback(widget)

    def button2_clicked(self):
        print("Abort and start over")
        widget = MainPage(self.callback)
        print(repr(Status.FIXED))
        widget.setStyleSheet(" background-color: rgb(0, 110, 0);")
        self.callback(widget)

    def button3_clicked(self):
        widget = SignalsDisplay(self.callback)
        self.callback(widget)
        widget.setStyleSheet(" background-color: rgb(0, 110, 0);")
        print("Button 3 clicked")

class InterlockDisplay(QFrame):
    def __init__(self, callback):
        super(InterlockDisplay,self).__init__()
        self.callback = callback
        widget = QWidget(self)
        textLabel = QLabel(widget)
        textLabel.setText("Error: Interlock is open.")
        textLabel.move(64,70) 
        font = textLabel.font()
        font.setPointSize(35)
        textLabel.setFont(font)
        textLabel.adjustSize()
        widget.setStyleSheet("color: rgb(250, 250, 250);")

        textLabel1 = QLabel(widget)
        textLabel1.setText("Close the enclosure door. ")
        textLabel1.move(64,135) 
        font = textLabel1.font()
        font.setPointSize(35)
        textLabel1.setFont(font)
        textLabel1.adjustSize()

        self.button1 = QPushButton(self)
        self.button1.setText("Clear error")
        self.button1.move(100,330)
        self.button1.resize(100, 300)
        self.button1.setStyleSheet(" background-color: rgb(171, 171, 171); \
        border-style: outset; \
        border-width: 2px;\
        border-radius: 10px; \
        border-color: beige; \
        font: bold 30px; \
        min-width: 10em; \
        padding: 6px;")
        self.button1.clicked.connect(self.button1_clicked)

        self.button2 = QPushButton(self)
        self.button2.setText("Abort")
        self.button2.move(550,330)
        self.button2.resize(100, 300)
        self.button2.setStyleSheet(" background-color: rgb(171, 171, 171); \
        border-style: outset; \
        border-width: 2px;\
        border-radius: 10px; \
        border-color: beige; \
        font: bold 30px; \
        min-width: 10em; \
        padding: 6px;")
        self.button2.clicked.connect(self.button2_clicked)

        self.button3 = QPushButton(self)
        self.button3.setText("Signal Statuses")
        self.button3.move(600,650)
        self.button3.resize(100, 100)
        self.button3.setStyleSheet(" background-color: rgb(171, 171, 171); \
        border-style: outset; \
        border-width: 2px;\
        border-radius: 10px; \
        border-color: beige; \
        font: bold 30px; \
        min-width: 10em; \
        padding: 6px;")
        self.button3.clicked.connect(self.button3_clicked)

    def button1_clicked(self):
        widget = ErrorDisplay(self.callback)
        print(repr(Status.FIXED))
        widget.setStyleSheet(" background-color: rgb(0, 110, 0);")
        self.callback(widget)

    def button2_clicked(self):
        print("Abort and start over")
        widget = MainPage(self.callback)
        print(repr(Status.FIXED))
        widget.setStyleSheet(" background-color: rgb(0, 110, 0);")
        self.callback(widget)

    def button3_clicked(self):
        widget = SignalsDisplay(self.callback)
        self.callback(widget)
        widget.setStyleSheet(" background-color: rgb(0, 110, 0);")
        print("Button 3 clicked")

class PlacingDisplay(QFrame):
    def __init__(self, callback):
        super(PlacingDisplay,self).__init__()
        self.callback = callback
        widget = QWidget(self)
        textLabel = QLabel(widget)
        textLabel.setText("Error: Aruco markers cannot be found.")
        textLabel.move(64,70) 
        font = textLabel.font()
        font.setPointSize(35)
        textLabel.setFont(font)
        textLabel.adjustSize()
        widget.setStyleSheet("color: rgb(250, 250, 250);")

        textLabel1 = QLabel(widget)
        textLabel1.setText("Check the following:")
        textLabel1.move(64,135) 
        font = textLabel1.font()
        font.setPointSize(35)
        textLabel1.setFont(font)
        textLabel1.adjustSize()

        textLabel2 = QLabel(widget)
        textLabel2.setText("1) Carrier has top plate.")
        textLabel2.move(64,200) 
        font = textLabel2.font()
        font.setPointSize(35)
        textLabel2.setFont(font)
        textLabel2.adjustSize()

        textLabel3 = QLabel(widget)
        textLabel3.setText("2) Camera is clean.")
        textLabel3.move(64,265) 
        font = textLabel3.font()
        font.setPointSize(35)
        textLabel3.setFont(font)
        textLabel3.adjustSize()
        print(repr(Status.CAMERA_FATAL))

        self.button1 = QPushButton(self)
        self.button1.setText("Clear error")
        self.button1.move(100,330)
        self.button1.resize(100, 300)
        self.button1.setStyleSheet(" background-color: rgb(171, 171, 171); \
        border-style: outset; \
        border-width: 2px;\
        border-radius: 10px; \
        border-color: beige; \
        font: bold 30px; \
        min-width: 10em; \
        padding: 6px;")
        self.button1.clicked.connect(self.button1_clicked)

        self.button2 = QPushButton(self)
        self.button2.setText("Abort")
        self.button2.move(550,330)
        self.button2.resize(100, 300)
        self.button2.setStyleSheet(" background-color: rgb(171, 171, 171); \
        border-style: outset; \
        border-width: 2px;\
        border-radius: 10px; \
        border-color: beige; \
        font: bold 30px; \
        min-width: 10em; \
        padding: 6px;")
        self.button2.clicked.connect(self.button2_clicked)

        self.button3 = QPushButton(self)
        self.button3.setText("Status")
        self.button3.move(600,650)
        self.button3.resize(100, 100)
        self.button3.setStyleSheet(" background-color: rgb(171, 171, 171); \
        border-style: outset; \
        border-width: 2px;\
        border-radius: 10px; \
        border-color: beige; \
        font: bold 30px; \
        min-width: 10em; \
        padding: 6px;")
        self.button3.clicked.connect(self.button3_clicked)

    def button1_clicked(self):
        widget = ErrorDisplay(self.callback)
        print(repr(Status.FIXED))
        widget.setStyleSheet(" background-color: rgb(0, 110, 0);")
        self.callback(widget)

    def button2_clicked(self):
        print("Abort and start over")
        widget = MainPage(self.callback)
        print(repr(Status.FIXED))
        widget.setStyleSheet(" background-color: rgb(0, 110, 0);")
        self.callback(widget)

    def button3_clicked(self):
        widget = SignalsDisplay(self.callback)
        self.callback(widget)
        widget.setStyleSheet(" background-color: rgb(0, 110, 0);")
        print("Button 3 clicked")

class FullDisplay(QFrame):
    def __init__(self, callback):
        super(FullDisplay,self).__init__()
        self.callback = callback
        widget = QWidget(self)
        textLabel = QLabel(widget)
        textLabel.setText("Finish: Loading tray is full.")
        textLabel.move(64,70) 
        font = textLabel.font()
        font.setPointSize(50)
        textLabel.setFont(font)
        textLabel.adjustSize()
        widget.setStyleSheet("color: rgb(250, 250, 250);")
        print(repr(Status.TRAY_FULL))

        textLabel2 = QLabel(widget)
        textLabel2.setText("Please load an empty tray.")
        textLabel2.move(64,150) 
        font = textLabel2.font()
        font.setPointSize(50)
        textLabel2.setFont(font)
        textLabel2.adjustSize()

        self.button1 = QPushButton(self)
        self.button1.setText("New tray loaded")
        self.button1.move(300,300)
        self.button1.resize(100, 300)
        self.button1.setStyleSheet(" background-color: rgb(171, 171, 171); \
        border-style: outset; \
        border-width: 2px;\
        border-radius: 10px; \
        border-color: beige; \
        font: bold 30px; \
        min-width: 10em; \
        padding: 6px;")
        self.button1.clicked.connect(self.button1_clicked)

        self.button3 = QPushButton(self)
        self.button3.setText("Signal Statuses")
        self.button3.move(600,650)
        self.button3.resize(100, 100)
        self.button3.setStyleSheet(" background-color: rgb(171, 171, 171); \
        border-style: outset; \
        border-width: 2px;\
        border-radius: 10px; \
        border-color: beige; \
        font: bold 30px; \
        min-width: 10em; \
        padding: 6px;")
        self.button3.clicked.connect(self.button3_clicked)

    def button1_clicked(self):
        widget = ErrorDisplay(self.callback)
        print(repr(Status.FIXED))
        widget.setStyleSheet(" background-color: rgb(0, 110, 0);")
        self.callback(widget)

    def button3_clicked(self):
        widget = SignalsDisplay(self.callback)
        self.callback(widget)
        widget.setStyleSheet(" background-color: rgb(0, 110, 0);")
        print("Button 3 clicked")

class EmerStopDisplay(QFrame):
    def __init__(self, callback):
        super(EmerStopDisplay,self).__init__()
        self.callback = callback
        widget = QWidget(self)
        textLabel = QLabel(widget)
        textLabel.setText("Error: Printer fails to complete move")
        textLabel.move(64,70) 
        font = textLabel.font()
        font.setPointSize(35)
        textLabel.setFont(font)
        textLabel.adjustSize()
        widget.setStyleSheet("color: rgb(250, 250, 250);")
        textLabel.setAlignment(Qt.AlignCenter)
        textLabel.setAlignment(Qt.AlignVCenter)

        textLabel2 = QLabel(widget)
        textLabel2.setText("Check the following:")
        textLabel2.move(64,135) 
        font = textLabel2.font()
        font.setPointSize(35)
        textLabel2.setFont(font)
        textLabel2.adjustSize()
        textLabel2.setAlignment(Qt.AlignCenter)
        textLabel2.setAlignment(Qt.AlignVCenter)

        textLabel3 = QLabel(widget)
        textLabel3.setText("1) Printer is in the proper internal state.")
        textLabel3.move(64,200) 
        font = textLabel3.font()
        font.setPointSize(35)
        textLabel3.setFont(font)
        textLabel3.adjustSize()

        textLabel4 = QLabel(widget)
        textLabel4.setText("2) Linux USB/serial port is appropriately")
        textLabel4.move(64,265) 
        font = textLabel4.font()
        font.setPointSize(35)
        textLabel4.setFont(font)
        textLabel4.adjustSize()

        textLabel7 = QLabel(widget)
        textLabel7.setText("  configured.")
        textLabel7.move(64,330) 
        font = textLabel7.font()
        font.setPointSize(35)
        textLabel7.setFont(font)
        textLabel7.adjustSize()

        textLabel5 = QLabel(widget)
        textLabel5.setText("3) There are no greater-scope failures.")
        textLabel5.move(64,395) 
        font = textLabel5.font()
        font.setPointSize(35)
        textLabel5.setFont(font)
        textLabel5.adjustSize()

        textLabel6 = QLabel(widget)
        textLabel6.setText("Restart the machine.")
        textLabel6.move(64,500) 
        font = textLabel6.font()
        font.setPointSize(35)
        textLabel6.setFont(font)
        textLabel6.adjustSize()
        textLabel6.setAlignment(Qt.AlignVCenter)

        self.button3 = QPushButton(self)
        self.button3.setText("Signal Statuses")
        self.button3.move(600,650)
        self.button3.resize(100, 100)
        self.button3.setStyleSheet(" background-color: rgb(171, 171, 171); \
        border-style: outset; \
        border-width: 2px;\
        border-radius: 10px; \
        border-color: beige; \
        font: bold 30px; \
        min-width: 10em; \
        padding: 6px;")
        self.button3.clicked.connect(self.button3_clicked)

        print(repr(Status.EMERGENCY))

    def button3_clicked(self):
        widget = SignalsDisplay(self.callback)
        self.callback(widget)
        widget.setStyleSheet(" background-color: rgb(0, 110, 0);")
        print("Button 3 clicked")

class ChamferPartDisplay(QFrame):
    def __init__(self, callback):
        super(ChamferPartDisplay,self).__init__()
        self.callback = callback
        widget = QWidget(self)
        textLabel = QLabel(widget)
        textLabel.setText("Error: No chamfer detected")
        textLabel.move(64,70) 
        font = textLabel.font()
        font.setPointSize(35)
        textLabel.setFont(font)
        textLabel.adjustSize()
        widget.setStyleSheet("color: rgb(250, 250, 250);")

        textLabel2 = QLabel(widget)
        textLabel2.setText("Check the following:")
        textLabel2.move(64,135) 
        font = textLabel2.font()
        font.setPointSize(35)
        textLabel2.setFont(font)
        textLabel2.adjustSize()
        
        textLabel3 = QLabel(widget)
        textLabel3.setText("1) Any ball seat was misloaded")
        textLabel3.move(64,200) 
        font = textLabel3.font()
        font.setPointSize(35)
        textLabel3.setFont(font)
        textLabel3.adjustSize()

        textLabel4 = QLabel(widget)
        textLabel4.setText("Restart the machine.")
        textLabel4.move(64,265) 
        font = textLabel4.font()
        font.setPointSize(35)
        textLabel4.setFont(font)
        textLabel4.adjustSize()

        print(repr(Status.IVALID_PART))

        self.button1 = QPushButton(self)
        self.button1.setText("Clear error")
        self.button1.move(100,330)
        self.button1.resize(100, 300)
        self.button1.setStyleSheet(" background-color: rgb(171, 171, 171); \
        border-style: outset; \
        border-width: 2px;\
        border-radius: 10px; \
        border-color: beige; \
        font: bold 30px; \
        min-width: 10em; \
        padding: 6px;")
        self.button1.clicked.connect(self.button1_clicked)

        self.button2 = QPushButton(self)
        self.button2.setText("Abort")
        self.button2.move(550,330)
        self.button2.resize(100, 300)
        self.button2.setStyleSheet(" background-color: rgb(171, 171, 171); \
        border-style: outset; \
        border-width: 2px;\
        border-radius: 10px; \
        border-color: beige; \
        font: bold 30px; \
        min-width: 10em; \
        padding: 6px;")
        self.button2.clicked.connect(self.button2_clicked)

        self.button3 = QPushButton(self)
        self.button3.setText("Signal Statuses")
        self.button3.move(600,650)
        self.button3.resize(100, 100)
        self.button3.setStyleSheet(" background-color: rgb(171, 171, 171); \
        border-style: outset; \
        border-width: 2px;\
        border-radius: 10px; \
        border-color: beige; \
        font: bold 30px; \
        min-width: 10em; \
        padding: 6px;")
        self.button3.clicked.connect(self.button3_clicked)

    def button1_clicked(self):
        widget = ErrorDisplay(self.callback)
        print(repr(Status.FIXED))
        widget.setStyleSheet(" background-color: rgb(0, 110, 0);")
        self.callback(widget)

    def button2_clicked(self):
        print("Abort and start over")
        widget = MainPage(self.callback)
        print(repr(Status.FIXED))
        widget.setStyleSheet(" background-color: rgb(0, 110, 0);")
        self.callback(widget)
    
    def button3_clicked(self):
        widget = SignalsDisplay(self.callback)
        self.callback(widget)
        widget.setStyleSheet(" background-color: rgb(0, 110, 0);")
        print("Button 3 clicked")

class PauseDisplay(QFrame):
    def __init__(self, callback):
        super(PauseDisplay,self).__init__()
        self.callback = callback
        widget = QWidget(self)
        textLabel = QLabel(widget)
        textLabel.setText("Paused")
        textLabel.move(350,150) 
        font = textLabel.font()
        font.setPointSize(70)
        textLabel.setFont(font)
        textLabel.adjustSize()
        widget.setStyleSheet("color: rgb(250, 250, 250);")
        print(repr(Status.PAUSE))

        self.button1 = QPushButton(self)
        self.button1.setText("Resume")
        self.button1.move(100,300)
        self.button1.resize(100, 300)
        self.button1.setStyleSheet(" background-color: rgb(171, 171, 171); \
        border-style: outset; \
        border-width: 2px;\
        border-radius: 10px; \
        border-color: beige; \
        font: bold 30px; \
        min-width: 10em; \
        padding: 6px;")
        self.button1.clicked.connect(self.button1_clicked)

        self.button2 = QPushButton(self)
        self.button2.setText("Abort")
        self.button2.move(550,300)
        self.button2.resize(100, 300)
        self.button2.setStyleSheet(" background-color: rgb(171, 171, 171); \
        border-style: outset; \
        border-width: 2px;\
        border-radius: 10px; \
        border-color: beige; \
        font: bold 30px; \
        min-width: 10em; \
        padding: 6px;")
        self.button2.clicked.connect(self.button2_clicked)

        self.button3 = QPushButton(self)
        self.button3.setText("Signal Statuses")
        self.button3.move(600,650)
        self.button3.resize(100, 100)
        self.button3.setStyleSheet(" background-color: rgb(171, 171, 171); \
        border-style: outset; \
        border-width: 2px;\
        border-radius: 10px; \
        border-color: beige; \
        font: bold 30px; \
        min-width: 10em; \
        padding: 6px;")
        self.button3.clicked.connect(self.button3_clicked)

    def button1_clicked(self):
        widget = ErrorDisplay(self.callback)
        print(repr(Status.FIXED))
        widget.setStyleSheet(" background-color: rgb(0, 110, 0);")
        self.callback(widget)

    def button2_clicked(self):
        print("Abort and start over")
        widget = MainPage(self.callback)
        print(repr(Status.FIXED))
        widget.setStyleSheet(" background-color: rgb(0, 110, 0);")
        self.callback(widget)
    
    def button3_clicked(self):
        widget = SignalsDisplay(self.callback)
        self.callback(widget)
        widget.setStyleSheet(" background-color: rgb(0, 110, 0);")
        print("Button 3 clicked")


class SplitterDisplay(QFrame):
    def __init__(self, callback):
        super(SplitterDisplay,self).__init__()
        self.callback = callback
        widget = QWidget(self)
        textLabel = QLabel(widget)
        textLabel.setText("Error: No ball seat detected after split")
        textLabel.move(64,70) 
        font = textLabel.font()
        font.setPointSize(35)
        textLabel.setFont(font)
        textLabel.adjustSize()
        widget.setStyleSheet("color: rgb(250, 250, 250);")

        textLabel2 = QLabel(widget)
        textLabel2.setText("Check the following:")
        textLabel2.move(64,135) 
        font = textLabel2.font()
        font.setPointSize(35)
        textLabel2.setFont(font)
        textLabel2.adjustSize()
        
        textLabel3 = QLabel(widget)
        textLabel3.setText("1) No ball seat is stuck in splitter")
        textLabel3.move(64,200) 
        font = textLabel3.font()
        font.setPointSize(35)
        textLabel3.setFont(font)
        textLabel3.adjustSize()

        print(repr(Status.SPLITTER_STUCK))

        self.button1 = QPushButton(self)
        self.button1.setText("Clear error")
        self.button1.move(100,330)
        self.button1.resize(100, 300)
        self.button1.setStyleSheet(" background-color: rgb(171, 171, 171); \
        border-style: outset; \
        border-width: 2px;\
        border-radius: 10px; \
        border-color: beige; \
        font: bold 30px; \
        min-width: 10em; \
        padding: 6px;")
        self.button1.clicked.connect(self.button1_clicked)

        self.button2 = QPushButton(self)
        self.button2.setText("Abort")
        self.button2.move(550,330)
        self.button2.resize(100, 300)
        self.button2.setStyleSheet(" background-color: rgb(171, 171, 171); \
        border-style: outset; \
        border-width: 2px;\
        border-radius: 10px; \
        border-color: beige; \
        font: bold 30px; \
        min-width: 10em; \
        padding: 6px;")
        self.button2.clicked.connect(self.button2_clicked)

        self.button3 = QPushButton(self)
        self.button3.setText("Signal Statuses")
        self.button3.move(600,650)
        self.button3.resize(100, 100)
        self.button3.setStyleSheet(" background-color: rgb(171, 171, 171); \
        border-style: outset; \
        border-width: 2px;\
        border-radius: 10px; \
        border-color: beige; \
        font: bold 30px; \
        min-width: 10em; \
        padding: 6px;")
        self.button3.clicked.connect(self.button3_clicked)

    def button1_clicked(self):
        widget = ErrorDisplay(self.callback)
        print(repr(Status.FIXED))
        widget.setStyleSheet(" background-color: rgb(0, 110, 0);")
        self.callback(widget)

    def button2_clicked(self):
        print("Abort and start over")
        widget = MainPage(self.callback)
        print(repr(Status.FIXED))
        widget.setStyleSheet(" background-color: rgb(0, 110, 0);")
        self.callback(widget)
    
    def button3_clicked(self):
        widget = SignalsDisplay(self.callback)
        self.callback(widget)
        widget.setStyleSheet(" background-color: rgb(0, 110, 0);")
        print("Button 3 clicked")

# SignalsDisplay provides live updates of all signals
class SignalsDisplay(QFrame):
    def __init__(self, callback):
        super(SignalsDisplay,self).__init__()
        self.callback = callback
        widget = QWidget(self)
        textLabel = QLabel(widget)
        textLabel.setText("Signal Statuses")
        textLabel.move(64,85)
        font = textLabel.font()
        font.setPointSize(50)
        textLabel.setFont(font) 
        textLabel.adjustSize()
        widget.setStyleSheet("color: rgb(250, 250, 250);")
        print(repr(Status.IN_USE))

        self.button1 = QPushButton(self)
        self.button1.setText("Click to go back")
        self.button1.move(600,650)
        self.button1.resize(100, 100)
        self.button1.setStyleSheet(" background-color: rgb(171, 171, 171); \
        border-style: outset; \
        border-width: 2px;\
        border-radius: 10px; \
        border-color: beige; \
        font: bold 30px; \
        min-width: 10em; \
        padding: 6px;")
        self.button1.clicked.connect(self.button1_clicked)

        self.createTable()
        self.layout = QVBoxLayout()
        self.layout.addWidget(self.tableWidget)
        self.setLayout(self.layout)

	#Create table
    def createTable(self):
        self.tableWidget = QTableWidget()

        #Row count
        self.tableWidget.setRowCount(7)

        #Column count
        self.tableWidget.setColumnCount(2)

        item = QTableWidgetItem("Signal Name")
        self.tableWidget.setItem(0,0,item)
        font = QtGui.QFont()
        font.setPointSize(30)
        font.setBold(True)
        font.setWeight(75)
        item.setFont(font)

        item = QTableWidgetItem("Value")
        self.tableWidget.setItem(0,1,item)
        item.setFont(font)

        item = QTableWidgetItem("Rolling Signal")
        self.tableWidget.setItem(1,0,item)
        font.setBold(False)
        item.setFont(font)
        
        item = QTableWidgetItem(str(ROLLING_STATUS))
        self.tableWidget.setItem(1,1,item)
        item.setFont(font)

        item = QTableWidgetItem("Orient Signal")
        self.tableWidget.setItem(2,0, item)
        item.setFont(font)

        item = QTableWidgetItem(str(ORIENT_STATUS))
        self.tableWidget.setItem(2,1,item)
        item.setFont(font)

        item = QTableWidgetItem("Placing Signal")
        self.tableWidget.setItem(3,0,item)
        item.setFont(font)

        item = QTableWidgetItem(str(PLACING_STATUS))
        self.tableWidget.setItem(3,1,item)
        item.setFont(font)

        item = QTableWidgetItem("Full Tray Signal")
        self.tableWidget.setItem(4,0,item)
        item.setFont(font)

        item = QTableWidgetItem(str(FULL_STATUS))
        self.tableWidget.setItem(4,1,item)
        item.setFont(font)

        item = QTableWidgetItem("Emergency Status")
        self.tableWidget.setItem(5,0,item)
        item.setFont(font)

        item = QTableWidgetItem(str(EMERGENCY_STATUS))
        self.tableWidget.setItem(5,1,item)
        item.setFont(font)

        item = QTableWidgetItem("Part Status")
        self.tableWidget.setItem(6,0,item)
        item.setFont(font)

        item =QTableWidgetItem(str(PART_STATUS))
        self.tableWidget.setItem(6,1,item)
        item.setFont(font)

        #Table will fit the screen horizontally
        # self.tableWidget.horizontalHeader().setStretchLastSection(True)
        self.tableWidget.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)

        self.tableWidget.setStyleSheet("QTableWidget {\n"
        "\n"
        "background-color:rgb(135, 212, 139)\n"
        "  \n"
        "\n"
        "\n"
        "\n"
        "}")

        self.tableWidget.resizeRowsToContents()

    def button1_clicked(self):
        widget = ErrorDisplay(self.callback)
        widget.setStyleSheet(" background-color: rgb(0, 110, 0);")
        self.callback(widget)

if __name__ == '__main__':

#def main_HMI():
    bg = threading.Thread(name='background', target=background)
    fg = threading.Thread(name='run_app', target=run_app)

    bg.start()
    run_app()
