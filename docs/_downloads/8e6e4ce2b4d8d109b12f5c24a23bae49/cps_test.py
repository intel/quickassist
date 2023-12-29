#!/usr/bin/env python3
import subprocess
import argparse
import re

# Initialize parser for command line arguments
parser = argparse.ArgumentParser()

# Adding optional arguments
parser.add_argument("-a", "--address", help = "Target address to connect to (default localhost)")

# Read arguments from command line
args = parser.parse_args()

if args.address:
    address = args.address
else:
    address = "localhost"

# Latency data is not collected with Connections Per Second tests
p50Latency = p75Latency = p99Latency = averageLatency = reqsPerSecond = requestCount = dataRead = transferPerSecond = 0

i = 1
while True:
    try:
        cmd = "./connection_test.sh " + address
        print(str(i) + ": Running: " + cmd)

        p = subprocess.Popen(cmd, shell=True, stdout = subprocess.PIPE,stderr = subprocess.PIPE,universal_newlines = True)
        p.wait()

        out,err = p.communicate()

        output = out.splitlines()
        for line in output:
            line = line.strip()
            if line.startswith("Connections per second:"):
                match = re.search(r"\d+(\.\d+)?", line)
                if (match):
                    reqsPerSecond = match.group()
                    print("reqsPerSecond: " + reqsPerSecond)

        telemetry_output="nginx_request_count " + str(requestCount) + "\nnginx_requests_per_second " + str(reqsPerSecond) + "\nnginx_data_read " + str(dataRead) + "\nnginx_transfers_per_second " + str(transferPerSecond) + "\nnginx_p50_latency " + str(p50Latency) + "\nnginx_p75_latency " + str(p75Latency) + "\nnginx_p99_latency " + str(p99Latency) + "\nnginx_ave_latency " + str(averageLatency) + "\n"

        with open('/var/lib/prometheus/node-exporter/textfile_collector/nginx.prom', 'w') as file:
        # Write new content to the prometheus log file for nginx
            file.write(telemetry_output)
        i+=1

    except KeyboardInterrupt:
        print("Stopping CPS tests")
        raise SystemExit

