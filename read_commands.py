import canlib.canlib as canlib
import socket
import struct
import time


def setUpChannel(channel=0,
                 openFlags=canlib.canOPEN_ACCEPT_VIRTUAL,
                 bitrate=canlib.canBITRATE_500K,
                 bitrateFlags=canlib.canDRIVER_NORMAL):
    cl = canlib.canlib()
    ch = cl.openChannel(channel, openFlags)
    print("Using channel: %s, EAN: %s" % (ch.getChannelData_Name(),
                                          ch.getChannelData_EAN()))
    ch.setBusOutputControl(bitrateFlags)
    ch.setBusParams(bitrate)
    ch.busOn()
    return ch


def tearDownChannel(ch):
    ch.busOff()
    ch.close()


class FrameType:
    """ Enumerates the types of CAN frames """
    DataFrame = 1
    RemoteFrame = 2
    ErrorFrame = 3
    OverloadFrame = 4


class Frame(object):
    """ Represents a CAN Frame
    Attributes:
        arb_id (int): Arbitration identifier of the Frame
        data (list of int): CAN data bytes
        frame_type (int): type of CAN frame
        is_extended_id (bool): is this frame an extended identifier frame?
    """

    def __init__(self, arb_id, data=None, frame_type=FrameType.DataFrame,
                 is_extended_id=False, interface=None, timestamp=None):
        """ Initializer of Frame
        Args:
            arb_id (int): identifier of CAN frame
            data (list, optional): data of CAN frame, defaults to empty list
            frame_type (int, optional): type of frame, defaults to
                                        FrameType.DataFrame
            is_extended_id (bool, optional): is the frame an extended id frame?
                                             defaults to False
            interface (string, optional): name of the interface the frame is on
                                          defaults to None
            ts (float, optional): time frame was received at
                                  defaults to None
        """

        self.is_extended_id = is_extended_id
        self.arb_id = arb_id
        if data:
            self.data = data
        else:
            self.data = []
        self.frame_type = frame_type
        self.interface = interface
        self.timestamp = timestamp

    @property
    def arb_id(self):
        return self._arb_id

    @arb_id.setter
    def arb_id(self, value):
        # ensure value is an integer
        assert isinstance(value, int), 'arbitration id must be an integer'
        # ensure standard id is in range
        if value >= 0 and value <= 0x7FF:
            self._arb_id = value
        # otherwise, check if frame is extended
        elif self.is_extended_id and value > 0x7FF and value <= 0x1FFFFFFF:
            self._arb_id = value
        # otherwise, id is not valid
        else:
            raise ValueError('Arbitration ID out of range')

    @property
    def data(self):
        return self._data

    @data.setter
    def data(self, value):
        # data should be a list
        assert isinstance(value, list), 'CAN data must be a list'
        # data can only be 8 bytes maximum
        assert not len(value) > 8, 'CAN data cannot contain more than 8 bytes'
        # each byte must be a valid byte, int between 0x0 and 0xFF
        for byte in value:
            assert isinstance(byte, int), 'CAN data must consist of bytes'
            assert byte >= 0 and byte <= 0xFF, 'CAN data must consist of bytes'
        # data is valid
        self._data = value

    @property
    def frame_type(self):
        return self._frame_type

    @frame_type.setter
    def frame_type(self, value):
        assert value == FrameType.DataFrame or value == FrameType.RemoteFrame \
            or value == FrameType.ErrorFrame or \
            value == FrameType.OverloadFrame, 'invalid frame type'
        self._frame_type = value

    @property
    def dlc(self):
        return len(self.data)

    def __str__(self):
        return ('ID=0x%03X, DLC=%d, Data=[%s]' %
                (self.arb_id, self.dlc, ', '.join(('%02X' % b)
                                                  for b in self.data)))

    def __eq__(self, other):
        return (self.arb_id == other.arb_id and
                self.data == other.data and
                self.frame_type == other.frame_type and
                self.is_extended_id == other.is_extended_id)


class SocketCanDev:
    def __init__(self, ndev):
        self.running = False

        if not hasattr(socket, 'PF_CAN') or not hasattr(socket, 'CAN_RAW'):
            print("Python 3.3 or later is needed for native SocketCan")
            raise SystemExit(1)

        self.socket = socket.socket(socket.PF_CAN, socket.SOCK_RAW,
                                    socket.CAN_RAW)
        self.ndev = ndev

    def start(self):
        self.socket.bind((self.ndev,))
        self.start_time = time.time()
        self.running = True

    def stop(self):
        pass

    def recv(self):
        assert self.running, 'device not running'
        frame_format = "=IB3xBBBBBBBB"
        frame_size = struct.calcsize(frame_format)

        frame_raw = self.socket.recv(frame_size)
        arb_id, dlc, d0, d1, d2, d3, d4, d5, d6, d7 = (
            struct.unpack(frame_format, frame_raw))

        # adjust the id and set the extended id flag
        is_extended = False
        if arb_id & 0x80000000:
            arb_id &= 0x7FFFFFFF
            is_extended = True

        frame = Frame(arb_id, is_extended_id=is_extended)
        # select the data bytes up to the DLC value
        frame.data = [d0, d1, d2, d3, d4, d5, d6, d7][0:dlc]
        frame.timestamp = time.time() - self.start_time

        return frame

    def send(self, frame):
        assert self.running, 'device not running'
        frame_format = "=IBBBBBBBBBBBB"

        # set the extended bit if a extended id is used
        arb_id = frame.arb_id
        if frame.is_extended_id:
            arb_id |= 0x80000000

        # get data, padded to 8 bytes
        data = frame.data + [0] * (8 - len(frame.data))
        packet = struct.pack(frame_format, arb_id, frame.dlc, 0xff, 0xff, 0xff,
                             data[0], data[1], data[2], data[3],
                             data[4], data[5], data[6], data[7])
        self.socket.send(packet)


# main code
cl = canlib.canlib()
print("canlib version: %s" % cl.getVersion())


channel_0 = 0
ch0 = setUpChannel(channel=0)

dev_send = SocketCanDev('vcan0')
dev_send.start()

while True:
    try:
        (msgId, msg, dlc, flg, time) = ch0.read()    
        data = [x for x in msg]
        frame = Frame(arb_id = msgId)
        frame._data = data
        #frame = Frame(arb_id = 947)
        #frame._data = [0,0,0,0,0,0,0,0]
        dev_send.send(frame)
    except (canlib.canNoMsg) as ex:
        None
    except (canlib.canError) as ex:
        print(ex)

tearDownChannel(ch0)
