# Efficient Parallel Real-time Map Matching Algorithm with High Accuracy
A parallel map matching algorithm which could handle 1,000 matching per second in each thread, and reached 97% accuracy under 5s GPS sampling rate by combining topology of roads and speed of vehicles

The format of source trajectory file is like:
{"latitude":39.83654,"devicesn":"967790112421","speed":0,"longitude":116.37153333333332,"direction":119,"timestamp":1425177688}
{"latitude":39.836528333333334,"devicesn":"967790112421","speed":0,"longitude":116.37171166666667,"direction":80,"timestamp":1425177694}
{"latitude":39.836595,"devicesn":"967790112421","speed":15.67,"longitude":116.37185,"direction":68,"timestamp":1425177697}
{"latitude":39.83672,"devicesn":"967790112421","speed":12.67,"longitude":116.37214833333334,"direction":82,"timestamp":1425177702}
{"latitude":39.836705,"devicesn":"967790112421","speed":9.01,"longitude":116.37233666666667,"direction":86,"timestamp":1425177704}
{"latitude":39.836585,"devicesn":"967790112421","speed":18.74,"longitude":116.37248,"direction":161,"timestamp":1425177709}
