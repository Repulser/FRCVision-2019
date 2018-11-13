import json
import math
import os

import cv2
import numpy as np

import netifaces as ni

from networktables import NetworkTables


persistent_file = 'global'


def default_value(name, folder):
    if folder is 'hsv':
        return {"H": (0, 255), "S": (0, 255), "V": (0, 255)}
    if folder is 'values':
        return {name+"_name": name}


def get_filename(name, folder):  # TODO: de-spaghettify
    return folder + "/{}.json".format(name)


def save_file(name, folder, data):
    with open(get_filename(name, folder), "w") as f:
        json.dump(data, f)


def load_file(name, folder):
    if not os.path.isfile(get_filename(name, folder)):
        save_file(name, folder, default_value(name, folder))
    with open(get_filename(name, folder), "r") as f:
        return json.load(f)


def aspect_ratio(width, height):
    return width / height


def circle_area(radius):
    return radius ** 2 * math.pi


def circle_ratio(cnt):
    _, radius = cv2.minEnclosingCircle(cnt)
    hull = cv2.convexHull(cnt)
    hull_area = cv2.contourArea(hull)
    return hull_area / float(circle_area(radius))


def hsv_mask(frame, hsv):
    hsv_colors = cv2.cvtColor(frame, cv2.COLOR_BGR2HSV)
    lower_hsv = np.array([hsv["H"][0], hsv["S"][0], hsv["V"][0]])
    higher_hsv = np.array([hsv["H"][1], hsv["S"][1], hsv["V"][1]])
    mask = cv2.inRange(hsv_colors, lower_hsv, higher_hsv)
    return mask


def morphology(mask, kernel):
    mask = cv2.morphologyEx(mask, cv2.MORPH_OPEN, kernel)
    mask = cv2.morphologyEx(mask, cv2.MORPH_CLOSE, kernel)
    return mask


def bitwise_mask(frame, mask):
    frame = frame.copy()
    return cv2.bitwise_and(frame, frame, mask=mask)


def contour_in_area(cnt1, cnt2):
    x1, y1, w1, h1 = cv2.boundingRect(cnt1)
    x2, y2, w2, h2 = cv2.boundingRect(cnt2)
    return x1 <= x2 <= x1 + w1 and y1 <= y2 <= y1 + h1


def calculate_fps(frame, current_time, last_time, avg):
    avg = (avg + (current_time - last_time)) / 2
    cv2.putText(frame, "{} FPS".format(int(1 / avg)), (0, 25), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 0, 0), 2, cv2.LINE_AA)
    return avg


def get_ip():
    ip = None
    while ip is None:
        for interface in ni.interfaces():
            try:
                addrs = ni.ifaddresses(interface)[ni.AF_INET]  # IPv4 addresses for current interface
                ip = addrs[0]['addr']  # The first IP address (probably the local one)
                if ip is not '127.0.0.1':
                    break
            except:
                ip = '0.0.0.0'

    return ip


def get_nt_server(team_number=5987):
    return "roboRIO-{}-FRC.local".format(team_number)


def nt_table():  # create the table and load all persistent values
    NetworkTables.initialize(server=get_nt_server())
    table = NetworkTables.getTable('SmartDashboard')
    return table  # TODO: test


def set_item(table, key, value):
    """
    Summary: Add a value to SmartDashboard.

    Parameters:
        * table: The current network table.
        * key : The name the value will be stored under and displayed.
        * value : The information the key will hold.
    """
    table.setDefaultValue(key, value)  # TODO: test
    print("value set")


def get_item(table, key, default_value):
    """
    Summary: Get a value from SmartDashboard.

    Parameters:
        * table: The current network table.
        * key : The name the value is stored under.
        * default_value : The value returned if key holds none.
    """
    return table.getValue(key, default_value)  # TODO: test


def set_values(table, name):  # load values from the associated file and add them to the table
    values = load_file(name, 'values')
    for key in values:
        set_item(table, key, values[key])
        print(key, values[key])


def get_values(table, name):  # save values from the table to the associated file
    table.saveEntries(filename=get_filename(name, 'values'), prefix=name+'_')


def clear_table(table):  # save all persistent values and clean the table of other values
    table.deleteAllEntries()
