# Set up can0 to get a dump of everything coming from the car.
sudo modprobe can
sudo modprobe can-raw
sudo modprobe can-dev
sudo modprobe vcan
sudo modprobe kvaser_usb
sudo ip link set can0 type can bitrate 500000
sudo ifconfig can0 up

# Set up vcan0 to filter out only some messages
# but still be able to use cansniffer and others.
sudo ip link add dev vcan0 type vcan
sudo ip link set up vcan0
