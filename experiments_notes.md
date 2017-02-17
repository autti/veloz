# Experiments Ford Fusion

##2017-02-15

command to filter ids in .log file in candump format

```sh
cat candump_files/amarillo.log | awk -F " " '{print $3}' | grep '4B0#\|202#' | python send_v2.py
```

Other notes:
* 202 id is related with steering command
* 216 id is related with GPS coordinates


##2017-02-16

I tried this command:

```sh
cat candump_files/amarillo.log | awk -F " " '{print $3}' | grep '186#\|18A#\|085#\|091#\|092#\|3CA#\|422#\|3A8#\|167#\|202#' | python send_v2.py
```

The command made the steeering wheel move a little bit. However, the pre-collision system was desactivated, the assistant break for slopes was desactivated. I tried the same command a second time, but there was no response of the steering wheel. The important parameters in the python script were:

* frame_repeat_period 0.0005
* frame_repeat_times 2

Apparently, the previous command move a little bit the steering wheel, but not always move it with the same angle 

Playing the frames from amarillo.log, using *frame_repeat_period* 0.01 and *frame_repeat_times* 1, provided the following results:

* 76: It shows sort of a steering wheel angle report.
* 415: Desactivated the transmission gear, reports speed, enable parking break in parking mode. It seems the command accelerates the car.
* 3CA: possible command for steering control?
* 216: moved GPS ? it activated the sonars in the panel.
