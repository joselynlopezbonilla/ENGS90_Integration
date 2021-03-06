#!/usr/bin/python3

import cv2 as cv
import serial
import numpy as np
from time import sleep
import math
import random
import gpiod

class Machine:
    def __init__(self):

        self.chip1=gpiod.Chip('gpiochip1')

        self.gripper_line=self.chip1.get_lines([18])

        self.gripper_line.request(consumer='pickandplace', type=gpiod.LINE_REQ_DIR_OUT, default_vals=[ 0 ])
        # Seek tolerance
        self.epsilon = 1.0

        #TODO: use this for smart adjustment of P parameter
        # Length of marker side in mm
        self.marker_length = 15.875
        # proportionality constant for pixels -> mm
        self.P = 15
        # Gripper vs camera centerpoint offset
        #gripper_offset = np.array([-42.0, -15.86])
        #gripper_offset = np.array([-54.0, -15.86])
        self.gripper_offset = np.array([-46.9, -16.2])

        print("Press ESC to end loop")
        cv.namedWindow("Preview")

        # Changes with testbench hardware
        self.cam = cv.VideoCapture("/dev/video0")
        self.ser = serial.Serial('/dev/ttyUSB0', 115200)

        self.cam.set(cv.CAP_PROP_BUFFERSIZE, 1)

        # Aruco initialization
        self.aruco_dict = cv.aruco.Dictionary_get(cv.aruco.DICT_4X4_50)
        self.aruco_params = cv.aruco.DetectorParameters_create()

        # Printer initialization
        print("Initializing printer...")
        self.ser.read_all()
        self.ser.write('\r\nG1\r\n'.encode())
        sleep(0.5)
        self.ser.readline()
        self.ser.read_all()
        self.ser.write('G91\r\n'.encode())
        print("Printer status: ", self.ser.readline())
        self.nominal_current = np.array([0, 0])
        # Currently relative to marker 1.
        self.offset_guesses = np.array([
            [-62, 108],
            [0, 0],
            [-100, 0],
            [-140, 80],
            ])
        self.offset_aruco_indices = [0, 1, 2, 1]
        self.station_hole_locs = [
                (12, self.get_hole_array),
                (12, self.get_hole_array),
                (12, self.get_hole_array),
                (1, self.get_station_offset),
                ]
    def get_station_offset(self, x, index):
        "Expects a normalized x variable"
        off = -25.0
        return off*x

    def get_image(self):
        # Exhaust the buffer TODO: find more elegant solution
        for i in range(0, 2):
            self.cam.grab()
        # Grab an image
        ret, frame = self.cam.read()
        return frame

    def move_rel(self, offset, rapid=False):
        # Send printer move command
        cmd = ''
        if rapid:
            cmd = 'G0 F50000 X{:.2f} Y{:.2f}\r\n'.format(offset[0], offset[1])
        else:
            cmd = 'G1 F2000 X{:.2f} Y{:.2f}\r\n'.format(offset[0], offset[1])
        #print("command sent to printer: ", cmd)
        self.ser.write(cmd.encode())
        #print("Printer response: ", self.ser.readline())
        # Wait for it to finish and then ask printer to confirm:
        cmd = 'M400\r\n'
        self.ser.write(cmd.encode())
        #print("Printer response: ", self.ser.readline())
        # Ask printer to confirm it's done moving.
        cmd = 'M118 move_done\r\n'
        self.ser.write(cmd.encode())
        i = 0
        while True:
            i = i + 1
            resp = self.ser.readline()
            if resp == b'move_done\r\n':
                break
            if i > 10:
                print("FAILED TO COMPLETE MOVE")
                break
            #print("Printer response: ", resp)
        self.nominal_current = self.nominal_current + offset
        #print("New nominal: ", nominal_current)

    def get_markers(self, marker):
        frame = self.get_image()
        markerCorners, markerIds, rejectedCandidates = \
                cv.aruco.detectMarkers(frame, self.aruco_dict, parameters=self.aruco_params)
        tid = -1
        minotnone = (markerIds != None)
        #print(minotnone, minotnone and len(markerIds) > 0)
        if minotnone and len(markerIds) > 0:
            markerIds = markerIds.squeeze(axis=1)
            #print("squozen: ", markerIds)
            try:
                tid = markerIds.tolist().index(marker)
            except ValueError:
                tid = -1
            #print("ntid: ", tid)
        return frame, tid, markerIds, markerCorners


    # Homes onto specified axis. Returns 0 if successful, otherwise 1 for error.
    def home_marker(self, marker, hole_index=-1):
        marker_nominal = marker
        marker = self.offset_aruco_indices[marker]
        # Look up guessed offset
        offset = self.offset_guesses[marker_nominal] - self.nominal_current
        self.move_rel(offset, rapid=True)
        timeout = 0
        # Loop to localize it
        out_marker_corners = None
        # Precompute setpoint
        center = np.array([0, 0])
        while True:
            frame, tid, markerIds, markerCorners = self.get_markers(marker)
            output = frame.copy()
            cv.aruco.drawDetectedMarkers(output, markerCorners, markerIds)
            cv.imshow("Preview", output)
            if tid == -1:
                if timeout < 10:
                    sleep(0.05)
                    timeout = timeout + 1
                    continue
                else:
                    print("Didn't find marker {}!".format(marker))
                    return 1
            #print("corners", markerCorners[tid])
            out_marker_corners = markerCorners[tid]
            centroid = np.sum(markerCorners[tid], 1)/4
            centroid = centroid[0]
            #print("centroid", centroid)
            #print("frame.shape", frame.shape)
            center = np.array([frame.shape[1]*2, frame.shape[0]])/3
            #print("center", center)
            # Make relative to center of image
            offset = center-centroid
            # Flips camera coord to printer coord
            offset[1] = -offset[1]
            #offset[0] = -offset[0]
            #print("offset", offset)
            # Are we sufficiently close?
            if np.linalg.norm(offset) < self.epsilon:
                break
            # Ease in to the setpoint
            offset = offset/self.P
            self.move_rel(offset)
        # find marker-space X axis
        if out_marker_corners is None:
            print("No found output corners!!!")
            return 1
        if hole_index < 0:
            return 0 # No hole requested
        x = np.array([0.0, 0.0])
        centroid = np.array([0.0, 0.0])
        averaging_frames = 4
        for i in range(averaging_frames):
            output = frame.copy()
            cv.aruco.drawDetectedMarkers(output, markerCorners, markerIds)
            cv.imshow("Preview", output)
            cv.waitKey(100)
            frame, tid, markerIds, markerCorners = self.get_markers(marker)
            if tid < 0:
                continue
            out_marker_corners = markerCorners[tid]
            # Average centroid too
            frame_centroid = np.sum(out_marker_corners, 1)/4
            centroid = centroid + frame_centroid[0]
            # corners are counterclockwise
            out_marker_corners = out_marker_corners.squeeze()
            x1 = out_marker_corners[0] - out_marker_corners[1]
            x2 = out_marker_corners[3] - out_marker_corners[2]
            # Average to get vector with length of side in direction of X
            x = x + (x1 + x2)/2
        x = x/np.linalg.norm(x)
        centroid = centroid/averaging_frames
        final_offset = center-centroid
        final_offset[1] = -final_offset[1]
        centroid_norm = np.linalg.norm(centroid)
        x_norm = np.linalg.norm(x)
        final_offset_norm = np.linalg.norm(final_offset)
        print('------------------------------')
        print(f'centroid norm: {centroid_norm}')
        print(f'x norm: {x_norm}')
        print(f'final offset norm: {final_offset_norm}')
        #TODO see comment in params section
        # go to specified hole
        n, loclookup = self.station_hole_locs[marker_nominal]
        if (hole_index >= n):
            print(f'Out of range hole index {hole_index}, only {n} holes, index < n:', hole_index < n)
            return 1
        hole_pos = loclookup(x, hole_index)
        self.move_rel(hole_pos + self.gripper_offset - final_offset)
        return 0

    def get_hole_array(x, index):
        # TODO allow multiple rings of holes
        radius = 23.876
        n = 12
        theta = 2*math.pi*index/n
        # re-scale X so it is of length radius
        x = x/np.linalg.norm(x)*radius
        # Rotate X by theta
        xx = x[0]*math.cos(theta) - x[1]*math.sin(theta)
        xy = x[0]*math.sin(theta) + x[1]*math.cos(theta)
        hole_pos = np.array([xx, xy])
        return hole_pos


    def reset_coords(self):
        self.nominal_current = np.array([0, 0])

    # set up to 0 to go down, up to 1 to go up.
    def pick(self, up=0):
        cmds =  ['G1 F200 Z-3', 'G1 F200 Z3']
        cmd = cmds[up]
        print("command sent to printer: ", cmd)
        self.ser.write(cmd.encode())
        print("Printer response: ", self.ser.readline())
        # Wait for it to finish and then ask printer to confirm:
        cmd = 'M400\r\n'
        self.ser.write(cmd.encode())
        print("Printer response: ", self.ser.readline())
        # Ask printer to confirm it's done moving.
        cmd = 'M118 move_done\r\n'
        self.ser.write(cmd.encode())
        i = 0
        while True:
            i = i + 1
            resp = self.ser.readline()
            if resp == b'move_done\r\n':
                break
            if i > 10:
                print("FAILED TO COMPLETE MOVE")
                break
            print("Printer response: ", resp)

    def run_demo(self):
        frame = self.get_image()
        offset = [0, 0]
        markerCorners, markerIds, rejectedCandidates = cv.aruco.detectMarkers(frame, self.aruco_dict, parameters=self.aruco_params)
        output = frame.copy()
        cv.aruco.drawDetectedMarkers(output, markerCorners, markerIds)
        cv.imshow("Preview", output)
        print("DEMO MODE ACTIVE")
        while True:
            # Pickup station
            self.home_marker(3, hole_index=0)
            self.gripper_line.set_values([1])
            frame = self.get_image()
            cv.imshow("Preview", frame)
            self.pick(0)
            if cv.waitKey(500) == 27:
                break
            self.pick(1)
            # Random Dropoff
            hole = random.randint(0, 11)
            carrier = random.randint(0, 2)
            self.home_marker(carrier, hole_index=hole)
            self.gripper_line.set_values([0])
            frame = self.get_image()
            cv.imshow("Preview", frame)
            self.pick(0)
            if cv.waitKey(500) == 27:
                break
            self.pick(1)
        

    def run(self):
        while True:
            frame = self.get_image()
            offset = [0, 0]
            markerCorners, markerIds, rejectedCandidates = cv.aruco.detectMarkers(frame, self.aruco_dict, parameters=self.aruco_params)
            output = frame.copy()
            cv.aruco.drawDetectedMarkers(output, markerCorners, markerIds)
            cv.imshow("Preview", output)
            key =  cv.waitKey(20)
            if key == 27:#ESC
                break
            elif key ==  82:#UP
                offset = [0, 20]
            elif key == 84:#DOWN
                offset = [0, -20]
            elif key == 81:#LEFT
                offset = [-20, 0]
            elif key == 83:#RIGHT
                offset = [20, 0]
            elif key == 48:# ZERO
                self.home_marker(0)
                self.gripper_line.set_values([0])
            elif key == 49:# ONE
                self.home_marker(1)
                self.gripper_line.set_values([0])
            elif key == 50:# TWO
                self.home_marker(2)
                self.gripper_line.set_values([0])
            elif key == 51:# THREE
                self.home_marker(3, hole_index=0)
                self.pick(0)
                self.gripper_line.set_values([1])
                cv.waitKey(20000)
                self.pick(1)
            elif key == 52:# FOUR
                self.home_marker(2, hole_index=0)
                self.pick(0)
                sleep(3)
                cv.waitKey(20000)
                self.pick(1)
            elif key == 122:# z
                self.reset_coords()
                self.move_rel(offset)
            elif key == 100:# d
                print("DEMO MODE ACTIVE")
                while True:
                    # Pickup station
                    self.home_marker(3, hole_index=0)
                    self.gripper_line.set_values([1])
                    frame = self.get_image()
                    cv.imshow("Preview", frame)
                    self.pick(0)
                    if cv.waitKey(500) == 27:
                        break
                    self.pick(1)
                    # Random Dropoff
                    hole = random.randint(0, 11)
                    carrier = random.randint(0, 2)
                    self.home_marker(carrier, hole_index=hole)
                    self.gripper_line.set_values([0])
                    frame = self.get_image()
                    cv.imshow("Preview", frame)
                    self.pick(0)
                    if cv.waitKey(500) == 27:
                        break
                    self.pick(1)
            else:#all others
                #print(key)
                pass
            if np.linalg.norm(offset) > 0.1:
                self.move_rel(offset, rapid=True)

    def stop(self):
        self.cam.release()

# machine = Machine()
# machine.run()
