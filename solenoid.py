#!/usr/bin/python3

from time import sleep
import gpiod

chip1=gpiod.Chip('gpiochip1')

gripper_line=chip1.get_lines([18])

gripper_line.request(consumer='pickandplace', type=gpiod.LINE_REQ_DIR_OUT, default_vals=[ 0 ])

while True:
    gripper_line.set_values([0])
    sleep(4)
    gripper_line.set_values([1])
    sleep(2)
