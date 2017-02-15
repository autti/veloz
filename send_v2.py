import sys
import struct
import time
import canlib.canlib as canlib


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


def parse(frame):
    """
    Receives a string and returns id, data.
      frame: String input (e.g. 415#19E6D0F907FA07FA
)
    Output
    id (hex), data ([hex])
    """
    str_id, str_data = frame.split("#")

    assert len(str_data) == 16

    list_data = [str_data[0:2], str_data[2:4],
                 str_data[4:6], str_data[6:8],
                 str_data[8:10], str_data[10:12],
                 str_data[12:14], str_data[14:16]]
 
    data = [int(item, 16) for item in list_data]
    
    return int(str_id, 16), data           


if __name__=="__main__":
    ch0 = setUpChannel(0) 
    # perhaps we need to repeat every frame a number of times
    # before moving on to the next one, in order to silence the car's conflicting commands.
    frame_repeat_period = 0.01
    frame_repeat_times = 10
    delay = frame_repeat_period *frame_repeat_times

    for line in sys.stdin:
        frame = line.strip()

        # Ignore blank lines
        if len(frame) != 20:
            continue
    
        arb_id, data = parse(frame)
        try:
            for i in range(frame_repeat_times):
                ch0.write(arb_id, data)
                time.sleep(frame_repeat_period)
                print arb_id, data
        except (canlib.canError) as ex:
            print(ex)
