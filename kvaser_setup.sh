sudo modprobe can
sudo modprobe can-raw
sudo modprobe can-dev
sudo modprobe kvaser_usb
sudo ip link set can0 type can bitrate 500000
sudo ifconfig can0 up

sudo modprobe vcan
sudo ip link add name vcan0 type vcan
sudo ifconfig vcan0 up

sudo ip link add name vcan1 type vcan
sudo ifconfig vcan1 up
