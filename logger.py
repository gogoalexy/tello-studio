import csv
import datetime
import re

import cv2

class DataLogger:

    pattern = re.compile(r'(-?\d+(?:\.\d+)?)')
    default_data_slice = {'timestamp': 'NA', 'mid': 'NA', 'x': 'NA', 'y': 'NA', 'z': 'NA', 'mpry': 'NA', 'pitch': 'NA', 'roll': 'NA', 'yaw': 'NA', 'vgx': 'NA', 'vgy': 'NA', 'vgz': 'NA', \
            'templ': 'NA', 'temph': 'NA', 'tof': 'NA', 'h': 'NA', 'bat': 'NA', 'baro': 'NA', \
            'time': 'NA', 'agx': 'NA', 'agy': 'NA', 'agz': 'NA'}
    fieldnames = ['timestamp', 'mid', 'x', 'y', 'z', 'mpry', 'pitch', 'roll', 'yaw', 'vgx', 'vgy', 'vgz', 'templ', 'temph', 'tof', 'h', 'bat', 'baro', 'time', 'agx', 'agy', 'agz']
    
    def __init__(self, drone, log_path):
        self.tello = drone
        ts = datetime.datetime.now()
        self.path_to_file = log_path + "{}.csv".format(ts.strftime("%Y-%m-%d_%H-%M-%S"))
        self.log_file = open(self.path_to_file, 'w', newline='')
        self.writer = csv.DictWriter(self.log_file, fieldnames=DataLogger.fieldnames)
        self.writer.writeheader()

    def close(self):
        self.log_file.close()
    
    @staticmethod
    def now():
        return datetime.datetime.now().timestamp()

    @staticmethod
    def parse(response):
        try:
            data_string = response.decode('utf-8')
            parsed = DataLogger.pattern.findall(data_string)
            data_slice = \
                {'timestamp': DataLogger.now(), 'mid': int(parsed[0]), 'x': int(parsed[1]), 'y': int(parsed[2]), 'z': int(parsed[3]), 'mpry': ','.join([parsed[4], parsed[5], parsed[6]]), \
                'pitch': int(parsed[7]), 'roll': int(parsed[8]), 'yaw': int(parsed[9]), 'vgx': int(parsed[10]), 'vgy': int(parsed[11]), 'vgz': int(parsed[12]), \
                'templ': int(parsed[13]), 'temph': int(parsed[14]), 'tof': int(parsed[15]), 'h': int(parsed[16]), 'bat': int(parsed[17]), 'baro': float(parsed[18]), \
                'time': int(parsed[19]), 'agx': float(parsed[20]), 'agy': float(parsed[21]), 'agz': float(parsed[22])}
        except:
            DataLogger.default_data_slice['timestamp'] = DataLogger.now()
            data_slice = DataLogger.default_data_slice
        return data_slice
    
    def is_data_string(self, response):
        if response == 'ok':
            return False
        else:
            return True

    def log_data(self):
        response = self.tello.get_response()
        if self.is_data_string(response):
            data_row = DataLogger.parse(response)
            self.writer.writerow(data_row)

    def log_command(self, command):
        pass

class Recorder:

    def __init__(self, log_path):
        ts = datetime.datetime.now()
        self.path_to_file = log_path + "{}.avi".format(ts.strftime("%Y-%m-%d_%H-%M-%S"))
        fourcc = cv2.VideoWriter_fourcc(*'XVID')
        self.video = cv2.VideoWriter(self.path_to_file, fourcc, 32.0, (960,720))

    def write(self, frame):
        bgrframe = cv2.cvtColor(frame, cv2.COLOR_RGB2BGR)
        self.video.write(bgrframe)

    def close(self):
        self.video.release()