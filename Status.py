from enum import Enum

class Status(Enum):
    # General states
    READY = "Machine is ready to begin cycle." #Done
    SET = "User has set chamfer mode." #Done
    TRAY_FULL = "Part placed correctly. Tray is full." #Done
    IN_USE = "Part placed correctly. Tray is not full." #Done
    EMERGENCY = "Emergency stop is activated." #Done
    FIXED = "Issue was addressed." #Done
    PAUSE = "Pause is activated." #Done 

    # Warnings and errors for rolling
    EMPTY = "No ball seats loaded in machine"

    # Warnings and errors for vision system and pick and place
    IVALID_PART = "Warning: No part detected." #Done
    INVALID_CHAMFER = "Warning: No chamfer detected." #Done
    CAMERA_FATAL = "Error: Camera visualization malfunction." #Done
    SPLITTER_STUCK = "Error: Ball seat stuck in splitter" #Done

    # Warnings and errors for orienting
    #Ian 's machine
    #Ball seats can get stuck
    #Ball seats are not introduced to it properly
    #Gustavo's machine is less likely to experience errors

