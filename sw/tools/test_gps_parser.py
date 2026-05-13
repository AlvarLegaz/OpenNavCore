from gps import GPSReader

gps = GPSReader(enabled=False)
gps.parse('$GPRMC,120000.00,A,4000.0000,N,00300.0000,W,1.0,90.0,130526,,,A*00')
print(gps.snapshot().to_dict())
