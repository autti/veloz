import struct
import socket
import time

class Bus:
    # message that belong to this bus
    _messages = []

    def add_message(self, message):
        assert isinstance(message, Message), 'invalid message'
        if message in self._messages:
            raise ValueError('Message %s already in bus' % message)
        else:
            self._messages.append(message)

    def remove_message(self, message):
        assert isinstance(Message, message), 'invalid message'
        try:
            self._messages.remove(message)
        except ValueError:
            raise ValueError('Message %s is not in bus' % message)

    def parse_frame(self, frame):
        assert isinstance(frame, Frame), 'invalid frame'
        for message in self._messages:
            if message.arb_id == frame.arb_id:
                return message.parse_frame(frame)

    def __str__(self):
        s = "Bus:\n"
        for message in self._messages:
            s = s + message.__str__()
        return s


class Message(object):
    # signals that belong to this message, indexed by start bit
    _signals = {}

    def __init__(self, name, arb_id):
        self.name = name
        self.arb_id = arb_id

    def add_signal(self, signal, start_bit):
        assert isinstance(signal, Signal), 'invalid signal'
        assert(isinstance(start_bit, int) and
               (start_bit < 63, 'invalid start bit'))
        self._signals[start_bit] = signal

    def remove_signal(self, signal):
        pass

    def parse_frame(self, frame):
        assert isinstance(frame, Frame), 'invalid frame'
        assert frame.arb_id == self.arb_id, 'frame id does not match msg id'

        # combine 8 data bytes into single value
        frame_value = 0
        for i in range(0, frame.dlc):
            if frame.data[i] is not None:
                frame_value = frame_value + (frame.data[i] << (8 * i))

        result_signals = []

        # iterate over signals
        for start_bit, signal in self._signals.items():

            # find the last bit of the singal
            end_bit = signal.bit_length + start_bit

            # compute the mask
            mask = 0
            for j in range(start_bit, end_bit):
                mask = mask + 2**j

            # apply the mask, then downshift
            value = (frame_value & mask) >> start_bit
            # pass the maksed value to the signal
            signal.parse_value(value)

            result_signals.append(signal)

        return result_signals

    def __str__(self):
        s = "Message: %s, ID: 0x%X\n" % (self.name, self.arb_id)
        for _, signal in self._signals.items():
            s = s + "\t" + signal.__str__() + "\n"
        return s


class Signal:
    def __init__(self, name, bit_length, factor=1, offset=0):
        self.name = name
        self.bit_length = bit_length
        self.factor = factor
        self.offset = offset
        self.value = 0

    def parse_value(self, value):
        self.value = value * self.factor + self.offset
        return self

    def __str__(self):
        s = "Signal: %s\tValue = %d" % (self.name, self.value)
        return s

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


##Signal: Steering Angle
# Max left
# Value = 24631
#[55, 96]
# Max rigt 
#Signal: Steering Angle
# Value = 8470
#[22, 33]
## 


def parse(db=None):
    if db is None:
        raise Exception('Please provide a dict with car config as the "db" param')
    # create a bus for this database
    b = Bus()
    for msg in db['messages']:
        # create a message
        m = Message(msg['name'], int(msg['id'], 0))

        # iterate over signals
        for start_bit, sig in msg['signals'].items():
            # create a signal
            s = Signal(sig['name'], sig['bit_length'])

            # parse offset and factor if set
            if 'offset' in sig:
                s.offset = int(sig['offset'])
            if 'factor' in sig:
                s.factor = float(sig['factor'])

	    # add this signal to the message
            m.add_signal(s, int(start_bit))

        # add this message to the bus
        b.add_message(m)

    return b

dev = SocketCanDev('vcan0')
dev.start()

dev_send = SocketCanDev('vcan1')
dev_send.start()

DECODER = {
    "messages": [
        {
        "name": "Steering Report",
        "id": "0x3A8",
        "signals": {
                    "16": {"name": "Steering Angle", "bit_length": 16},
                   }
        }
    ]
}



b = parse(db=DECODER)
filter = False

while True:
    frame =dev.recv()
    code = frame._arb_id
    data = frame._data
    timestamp = frame.timestamp
    hbeam_id = 0x83
    if code == hbeam_id and data[0] == 0x00:
        filter = True
    elif code == hbeam_id and data[0] == 0x00:
        filter = False

    if filter:
        msg = '(%s) %s#%s' % (timestamp, code, data)
        dev_send.send(frame)
        if code == 0x3A8:
            signals = b.parse_frame(frame)
            if signals:
                for s in signals:
                    print(s)
                    print(data[2:4])
