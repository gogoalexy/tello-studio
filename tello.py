import socket
import threading
import time
import numpy as np
import libh264decoder

# TODO: check out of range values and throw exceptions accordingly

class Tello:
    """Wrapper class to interact with the Tello drone."""

    def __init__(self, local_ip, local_port, command_timeout=.3, tello_ip='192.168.10.1',
                 tello_port=8889):
        """
        Binds to the local IP/port and puts the Tello into command mode.

        :param local_ip (str): Local IP address to bind.
        :param local_port (int): Local port to bind.
        :param command_timeout (int|float): Number of seconds to wait for a response to a command.
        :param tello_ip (str): Tello IP.
        :param tello_port (int): Tello port.
        """

        self.abort_flag = False
        self.decoder = libh264decoder.H264Decoder()
        self.command_timeout = command_timeout
        self.response = None  
        self.frame = None  # numpy array BGR -- current camera output frame
        self.is_freeze = False  # freeze current camera output
        self.last_frame = None
        self.local_ip = local_ip
        self.local_port = local_port
        self.tello_address = (tello_ip, tello_port)
        self.local_video_port = 11111  # port for receiving video stream
        self.last_height = 0
        
    def __del__(self):
        self.disconnect()

    def connect(self, streamon=True):
        self.connected = True

        self.socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)  # socket for sending cmd
        self.socket_video = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)  # socket for receiving video stream
        self.socket.bind((self.local_ip, self.local_port))

        # thread for receiving cmd ack
        self.receive_thread = threading.Thread(target=self._receive_thread)
        self.receive_thread.daemon = True

        self.receive_thread.start()

        # to receive video -- send cmd: command, streamon
        self.socket.sendto(b'command', self.tello_address)
        print ('sent: command')
       
        # TODO 
        time.sleep(5)
        
        if streamon:
            self.socket.sendto(b'streamon', self.tello_address)
            print ('sent: streamon')

        self.socket_video.bind(("0.0.0.0", self.local_video_port))

        # thread for receiving video
        self.receive_video_thread = threading.Thread(target=self._receive_video_thread)
        self.receive_video_thread.daemon = True

        self.receive_video_thread.start()


    def disconnect(self):
        if self.socket is not None:
            self.land()
            self.set_abort_flag()
            self.socket.close()

        if self.socket_video is not None:
            self.socket_video.close()

        self.connected = False
        self.socket = None
        self.socket_video = None
    
    def read(self):
        """Return the last frame from camera."""
        if self.is_freeze:
            return self.last_frame
        else:
            return self.frame

    def video_freeze(self, is_freeze=True):
        """Pause video output -- set is_freeze to True"""
        self.is_freeze = is_freeze
        if is_freeze:
            self.last_frame = self.frame

    def _receive_thread(self):
        """Listen to responses from the Tello.

        Runs as a thread, sets self.response to whatever the Tello last returned.

        """
        while self.connected:
            try:
                self.response, ip = self.socket.recvfrom(3000)
            except socket.error as exc:
                print(("Caught exception socket.error : %s" % exc))

    def _receive_video_thread(self):
        """
        Listens for video streaming (raw h264) from the Tello.

        Runs as a thread, sets self.frame to the most recent frame Tello captured.

        """
        packet_data =b''
        while self.connected:
            try:
                res_string, ip = self.socket_video.recvfrom(2048)
                
                packet_data += res_string
                # end of frame
                if len(res_string) != 1460:
                    for frame in self._h264_decod(packet_data):
                        self.frame = frame
                    packet_data = b''
                        
            except socket.error as exc:
                print(("Caught exception socket.error : %s" % exc))
    
    
    def _h264_decod(self, packet_data):
        """
        decode raw h264 format data from Tello
        
        :param packet_data: raw h264 data array
       
        :return: a list of decoded frame
        """
        res_frame_list = []
        frames = self.decoder.decode(packet_data)
                 
        for framedata in frames:
            (frame, w, h, ls) = framedata
            if frame is not None:
                # print ('frame size %i bytes, w %i, h %i, linesize %i' % (len(frame), w, h, ls))
                frame = np.frombuffer(frame, dtype = np.ubyte, count = len(frame))
                frame = (frame.reshape((h, ls//3, 3)))
                frame = frame[:, :w, :]
                res_frame_list.append(frame)

        return res_frame_list

    def send_command(self, command):
        """
        Send a command to the Tello and wait for a response.

        :param command: Command to send.
        :return (str): Response from Tello.

        """

        print((">> send cmd: {}".format(command)))
        self.abort_flag = False
        timer = threading.Timer(self.command_timeout, self.set_abort_flag)

        self.socket.sendto(command.encode('utf-8'), self.tello_address)

        timer.start()
        while self.response is None:
            if self.abort_flag is True:
                break
        timer.cancel()
        
        if self.response is None:
            response = 'none_response'
        else:
            response = self.response.decode('latin-1')

        self.response = None

        print(response)
        return response
    
    def set_abort_flag(self):
        """
        Sets self.abort_flag to True.

        Used by the timer in Tello.send_command() to indicate to that a response
        
        timeout has occurred.

        """

        self.abort_flag = True

    def takeoff(self, delay=0):
        """
        Initiates take-off.

        Returns:
            str: Response from Tello, 'OK' or 'FALSE'.

        """

        resp = self.send_command('takeoff')
        time.sleep(delay)
        return resp

    def set_speed(self, speed):
        """
        Sets speed.

        The method expects speeds from
        1 to 100 centimeters/second.

        Args:
            speed (int): Speed.

        Returns:
            str: Response from Tello, 'OK' or 'FALSE'.

        """
        return self.send_command('speed %s' % speed)

    def rotate_cw(self, degrees, delay=0):
        """
        Rotates clockwise.

        Args:
            degrees (int): Degrees to rotate, 1 to 360.

        Returns:
            str: Response from Tello, 'OK' or 'FALSE'.

        """

        resp = self.send_command("cw " + str(degrees))
        time.sleep(delay)
        return resp

    def rotate_ccw(self, degrees, delay=0):
        """
        Rotates counter-clockwise.

        Args:
            degrees (int): Degrees to rotate, 1 to 360.

        Returns:
            str: Response from Tello, 'OK' or 'FALSE'.

        """
        resp = self.send_command('ccw %s' % degrees)
        time.sleep(delay)
        return resp

    def flip(self, direction, delay=0):
        """
        Flips.

        Args:
            direction (str): Direction to flip, 'l', 'r', 'f', 'b'.

        Returns:
            str: Response from Tello, 'OK' or 'FALSE'.

        """

        resp = self.send_command('flip %s' % direction)
        time.sleep(delay)
        return resp

    def get_response(self):
        """
        Returns response of tello.

        Returns:
            int: response of tello.

        """
        return self.response

    def get_height(self):
        """Returns height(dm) of tello.

        Returns:
            int: Height(dm) of tello.

        """
        height = self.send_command('height?')
        height = str(height)
        height = list(filter(str.isdigit, height))
        try:
            height = int(height)
            self.last_height = height
        except:
            height = self.last_height
            pass
        return height

    def get_battery(self):
        """Returns percent battery life remaining.

        Returns:
            int: Percent battery life remaining.

        """
        
        battery = self.send_command('battery?')

        try:
            battery = int(battery)
        except:
            pass

        return battery

    def get_flight_time(self):
        """Returns the number of seconds elapsed during flight.

        Returns:
            int: Seconds elapsed during flight.

        """

        flight_time = self.send_command('time?')

        try:
            flight_time = int(flight_time)
        except:
            pass

        return flight_time

    def get_speed(self):
        """Returns the current speed.

        Returns:
            int: Current speed in KPH.

        """

        speed = self.send_command('speed?')

        try:
            speed = float(speed)
            speed = round((speed / 27.7778), 1)
        except:
            pass

        return speed

    def land(self, delay=0):
        """Initiates landing.

        Returns:
            str: Response from Tello, 'OK' or 'FALSE'.

        """

        resp = self.send_command('land')
        time.sleep(delay)
        return resp

    def move(self, direction, distance, delay = 0):
        """Moves in a direction for a distance.

        This method expects meters or feet. The Tello API expects distances
        from 20 to 500 centimeters.

        Args:
            direction (str): Direction to move, 'forward', 'back', 'right' or 'left'.
            distance (int|float): Distance to move.

        Returns:
            str: Response from Tello, 'OK' or 'FALSE'.

        """

        resp = self.send_command('%s %s' % (direction, distance))
        time.sleep(delay)
        return resp

    def move_rc(self, lr, fb, ud, yaw):
        """Move drone according to 4 input channels

        Args:
            lr (int): left/right (-100 - 100)
            fb (int): forward/backward (100 - -100)
            ud (int): up/down (100 - -100)
            yaw (int): rotation (-100 - 100)

        Returns:
            str: Response from Tello, 'OK' or 'FALSE'.

        """

        lr = str(lr)
        fb = str(fb)
        ud = str(ud)
        yaw = str(yaw)

        return self.send_command('rc %s %s %s %s' % (lr, fb, ud, yaw))


    def move_backward(self, distance, delay=0):
        """Moves backward for a distance.

        See comments for Tello.move().

        Args:
            distance (int): Distance to move.

        Returns:
            str: Response from Tello, 'OK' or 'FALSE'.

        """

        return self.move('back', distance, delay)

    def move_down(self, distance, delay=0):
        """Moves down for a distance.

        See comments for Tello.move().

        Args:
            distance (int): Distance to move.

        Returns:
            str: Response from Tello, 'OK' or 'FALSE'.

        """

        return self.move('down', distance, delay)

    def move_forward(self, distance, delay=0):
        """Moves forward for a distance.

        See comments for Tello.move().

        Args:
            distance (int): Distance to move.

        Returns:
            str: Response from Tello, 'OK' or 'FALSE'.

        """
        return self.move('forward', distance, delay)

    def move_left(self, distance, delay=0):
        """Moves left for a distance.

        See comments for Tello.move().

        Args:
            distance (int): Distance to move.

        Returns:
            str: Response from Tello, 'OK' or 'FALSE'.

        """
        return self.move('left', distance, delay)

    def move_right(self, distance, delay=0):
        """Moves right for a distance.

        See comments for Tello.move().

        Args:
            distance (int): Distance to move.

        """
        return self.move('right', distance, delay)

    def move_up(self, distance, delay=0):
        """Moves up for a distance.

        See comments for Tello.move().

        Args:
            distance (int): Distance to move.

        Returns:
            str: Response from Tello, 'OK' or 'FALSE'.

        """

        return self.move('up', distance, delay)
