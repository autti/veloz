import click
import serial
import socket
import struct

def send(arb_id, data, device='can0'):
    """
    id: Can id in hex format
    data: Can data in hex format
    """
    if not hasattr(socket, 'PF_CAN') or not hasattr(socket, 'CAN_RAW'):
        print("Python 3.3 or later is needed for native SocketCan")
        raise SystemExit(1)

    sckt = socket.socket(socket.PF_CAN, socket.SOCK_RAW,
                                    socket.CAN_RAW)

    sckt.bind((device,))

    # get data, padded to 8 bytes
    data = data + [0] * (8 - len(data))
    frame_format = "=IB3xBBBBBBBB"
    dlc = len(data)
    packet = struct.pack(frame_format, arb_id, dlc,
                             data[0], data[1], data[2], data[3],
                             data[4], data[5], data[6], data[7])
    sckt.send(packet)


def format_message(arduino_string):
    """
    Receives a string from arduino and returns id, data, can
      input: "b'can@1@1440@0#17#0#68#0#0#0#0\r\n"
      output: 1440, [0,17,0,68,0,0,0,0], vcan1 
    """
    v_can = ""
    data = [0, 0, 0, 0, 0, 0, 0, 0]
    msg_id = 0

    ms = arduino_string.split('@')
    if ms[0][-3:] == 'can':
        v_can = 'vcan{}'.format(ms[1])
        list_data = ms[3][:-5].split('#') 
        data = [int(item) for item in list_data]
        msg_id = int(ms[2])
    return msg_id, data, v_can


@click.command()
def main():
    ser = serial.Serial('/dev/ttyACM2', 115200)
    while True:
        arduino_received = ser.readline()
        arduino_received = str(arduino_received)
        arb_id, data, v_device = format_message(arduino_received)
        if (v_device == "vcan0") or (v_device == "vcan1"):
            send(arb_id, data, device=v_device)


if __name__=="__main__":
    main()
