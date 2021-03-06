# Joselyn Lopez Bonilla
## ENGS90 Winter 2022

### HMI


The human-machine interaction (HMI) module for the Reorientation Machine is vital for user experience and for error handling. 
The `HMI` is controlled by both inputs from the machine and the user. The `HMI` is implemented in python using the PYQT5 library. 

### Usage

The *HMI* module, implemented in `HMI.py`, runs the HMI for the Reorintation Application, and exports the following classes:

```python
class ReorientationApp(QMainWindow):
class SplashScreen():
class MainPage(QFrame):
class ErrorDisplay(QFrame):
class RollingDisplay(QFrame):
class InterlockDisplay(QFrame):
class PlacingDisplay(QFrame):
class FullDisplay(QFrame):
class EmerStopDisplay(QFrame):
class ChamferPartDisplay(QFrame):
class PauseDisplay(QFrame):
class SplitterDisplay(QFrame):
class PickerDisplay(QFrame):
class SignalsDisplay(QFrame):
class SerialDisplay(QFrame):
class PrinterDisplay(QFrame):   
```

The *HMI* module also exports the following main functions:
```python
def background():
def run_app():
def main_HMI():
```

### Implementation

We implement this HMI as a series of classes and functions.

The `ReorientationApp` class assigns signals from other modules to a PYQT5 signal. It does this by using the following functions: `handleRMSignal`, `handleOMSignal`, `handlePMSignal`, `handleFMSignal`, `handleEMSignal`, `handlePartMSignal`, `handlePartSMSignal`, `handlePickerMSignal`, `handleSerialSignal`, and `handlePrinterSignal`. Each of these functions then call their respective widgets to be displayed for the user on the HMI screen. 

The `SplashScreen` class displays a widget as the machine powers up.

The `MainPage` class displays a widget where the user can define the orientation of the chamfer (chamfer side-up or chamfer side-down). The class contains two functions `button1_clicked` and `button2_clicked` to aid with the functionality of buttons on the display.

The `ErrorDisplay` class displays a widget that waits for an update signal. This is the default widget screen, and the user may pause normal operation. The class contains a function `button1_clicked` to aid with the functionality of buttons on the display.

The `RollingDisplay` class displays an error widget that signifies a part was not able to be placed in a rolling manner or that the rolling filter is stuck. The user will be able to dismiss the error with a button press on the screen. The class contains a function `button1_clicked` to aid with the functionality of the button on the display.

The `InterlockDisplay` class displays an error widget that signifies the enclosure door is open. The user will be able to dismiss the warning with a button press on the screen. The class contains a function `button1_clicked` to aid with the functionality of the button on the display.

The `PlacingDisplay` class displays an error widget that signifies a part was not able to be placed onto the tray. The user will be able to dismiss error with a button press on the screen. The class contains a function `button1_clicked` to aid with the functionality of the button on the display.

The `FullDisplay` class displays an done widget that signifies a tray has been completed. the user will be able to dismiss the update with a button press on the screen once a new tray has been placed. The class contains a function `button1_clicked` to aid with the functionality of the button on the display.

The `ChamferPartDisplay` class displays an error widget that signifies a chamfer cannot be detected. The user will be able to dismiss error with a button press on the screen. The class contains a function `button1_clicked` to aid with the functionality of the button on the display.

The `PauseDisplay` class displays a widget when the user has indicated to pause the machine. User will be able to resume or abort the task. The class contains two functions `button1_clicked` and `button2_clicked` to aid with the functionality of buttons on the display.

The `SplitterDisplay` class displays an error widget that signifies a ball seat is not found after the splitter. The user will be able to dismiss error with a button press on the screen. The class contains a function `button1_clicked` to aid with the functionality of the button on the display.

The `PickerDisplay` class displays an error widget that signifies the picker cannot move along the z-axis. The user will be able to dismiss error with a button press on the screen. The class contains a function `button1_clicked` to aid with the functionality of the button on the display.

The `SerialDisplay` class displays an error widget that signifies the serial port is incorrect. The user will need to edit `seek.py` and rerun the program. 

The `PrinterDisplay` class displays an error widget that signifies when the machine is in the wrong internal state. The user will need to restart the machine. 

All display functions have an internal function `button3_clicked` that connects the button press to the tabulation of signals. 

The `background` function polls the signals from the machine.

The `run_app` function contains the application and widgets to be displayed on the HMI screen.

The `main_HMI` function runs a thread of both the run_app and background functions.

The program terminates when power is shut off either manually or by using the emergency button. The program can also terminate when the user has aborted the task. 

### Assumptions

No assumptions beyond those that are clear from the spec.

### Files

* `HMI.py` - the implementation

### Compilation

To compile, simply `sudo python3 HMI.py` for integrated HMI.