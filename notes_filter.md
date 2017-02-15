### Filter

command to filter ids in .log file in candump format

```sh
cat candump_files/amarillo.log | awk -F " " '{print $3}' | grep '4B0#\|202#' | python send_v2.py
```

Other notes:
* 202 id is related with steering command
* 216 id is related with GPS coordinates
