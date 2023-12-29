#!/usr/bin/env python3
import subprocess
import argparse
import re

# Initialize parser for command line arguments
parser = argparse.ArgumentParser()

# Adding optional arguments
parser.add_argument("-f", "--file", help = "File to download")
parser.add_argument("-a", "--address", help = "address of nginx server")
parser.add_argument("-t", "--threads", help = "Number of threads (default 50)")
parser.add_argument("-n", "--connections", help = "Number of connections per thread (default 400)")
parser.add_argument("-d", "--duration", help = "Duration of the test in seconds (default 10)")
parser.add_argument("-R", "--rate", help = "Rate (default 10000)")
parser.add_argument("-c", "--compress", help = "Allow compressed files (default = False)")
parser.add_argument("-i", "--iterations", help = "Number of times to loop (default = 35)")

# Read arguments from command line
args = parser.parse_args()
if args.file:
    file = args.file
else:
    file = "silesia.concat.txt"
if args.threads:
    threads = int(args.threads)
else:
    threads = 20
if args.connections:
    connections = int(args.connections)
else:
    connections = 300
if args.address:
    address = args.address
else:
    address = "127.0.0.1"
if args.duration:
    duration = int(args.duration)
else:
    duration = 10
if args.rate:
    rate = int(args.rate)
else:
    rate = 10000
if args.compress:
    compress = 1
else:
    compress = 0
if args.iterations:
    iterations = int(args.iterations)
else:
    iterations = 35

p50Latency = p75Latency = p99Latency = convertAveLatency = 0

cmd = "numactl -C 20 wrk -t" + str(threads) + " -c" + str(connections) + " -d" + str(duration) + " -R" + str(rate) + " -L --timeout 60s "

if compress:
    cmd = cmd + "-H 'Accept-Encoding: gzip' "

cmd = cmd + 'https://' + address + '/' + file

i = 1
while i <= iterations:
    try:
        print(str(i) + ": Running: " + cmd)
        i += 1
        p = subprocess.Popen(cmd, shell=True, stdout = subprocess.PIPE,stderr = subprocess.PIPE,universal_newlines = True)
        p.wait()

        out,err = p.communicate()

        output = out.splitlines()
        dataRead = averageLatency = connectErrors = timeoutErrors = 0
        for line in output:
            line = line.strip()

            if line.__contains__("Socket errors:"):
                match = re.search(r"connect \d+", line)
                if (match):
                    connectErrorsString = match.group()
                    match = re.search(r"\d+", connectErrorsString)
                    if (match):
                        connectErrors = int(match.group())
                        print(str(connectErrors))

                match = re.search(r"timeout \d+", line)
                if (match):
                    timeoutErrorsString = match.group()
                    match = re.search(r"\d+", timeoutErrorsString)
                    if (match):
                        timeoutErrors = int(match.group())
                        print(str(timeoutErrors))
            elif line.startswith("50.000%"):
                match = re.search(r"\d+(\.\d+)?ms", line)
                if (match):
                    p50LatencyString = match.group()
                    match = re.search(r"\d+(\.\d+)?", p50LatencyString)
                    p50Latency = float(match.group())
                    convertAveLatency = False
                else:
                    match = re.search(r"\d+(\.\d+)?s", line)
                    if (match):
                        # Time was in seconds.. convert to ms
                        p50LatencyString = match.group()
                        match = re.search(r"\d+(\.\d+)?", p50LatencyString)
                        p50Latency = float(match.group()) * 1000
                        # since p50 latency is in seconds, set flag to convert Average Latency
                        convertAveLatency = True
            elif line.startswith("75.000%"):
                match = re.search(r"\d+(\.\d+)?ms", line)
                if (match):
                    p75LatencyString = match.group()
                    match = re.search(r"\d+(\.\d+)?", p75LatencyString)
                    p75Latency = float(match.group())
                else:
                    match = re.search(r"\d+(\.\d+)?s", line)
                    if (match):
                        # Time was in seconds.. convert to ms
                        p75LatencyString = match.group()
                        match = re.search(r"\d+(\.\d+)?", p75LatencyString)
                        p75Latency = float(match.group()) * 1000
            elif line.startswith("99.000%"):
                match = re.search(r"\d+(\.\d+)?ms", line)
                if (match):
                    p99LatencyString = match.group()
                    match = re.search(r"\d+(\.\d+)?", p99LatencyString)
                    p99Latency = match.group()
                else:
                    match = re.search(r"\d+(\.\d+)?s", line)
                    if (match):
                        # Time was in seconds.. convert to ms
                        p99LatencyString = match.group()
                        match = re.search(r"\d+(\.\d+)?", p99LatencyString)
                        p99Latency = float(match.group()) * 1000
            elif line.startswith("Latency"):
                match = re.search(r"Latency\s\s+\d+(\.\d+)?", line)
                if (match):
                    averageLatencyString = match.group()
                    match = re.search(r"\d+(\.\d+)?", averageLatencyString)
                    if (match):
                        averageLatency = match.group()
            elif line.startswith("Requests/sec:"):
                match = re.search(r"\d+(\.\d+)?", line)
                if (match):
                    reqsPerSecond = match.group()
            elif line.startswith("Transfer/sec:"):
                match = re.search(r"\d+(\.\d+)?", line)
                if (match):
                    transferPerSecond = match.group()
                    if line.__contains__("GB"):
                        transferPerSecond = float(transferPerSecond) * 1000
            else:
                match = re.search(r"\d+ requests in?", line)
                if (match):
                    requestCount = str(match.group()).split(' ')[0]
                match = re.search(r"\d+(\.\d+)GB?", line)
                if (match):
                    dataReadString = match.group()
                    match = re.search(r"\d+(\.\d+)?", dataReadString)
                    dataRead = match.group()
                else:
                    # Data Read in MB... convert to GB
                    match = re.search(r"\d+MB?", line)
                    if (match):
                        dataReadString = match.group()
                        match = re.search(r"\d+(\.\d+)?", dataReadString)
                        dataRead = float(match.group()) / 1000

        if convertAveLatency:
            if (float(averageLatency) < 1000):
                averageLatency = float(averageLatency) * 1000

        # logic to grab current request count and data read values and error counts.. so we can keep running total
        p = subprocess.Popen("cat /var/lib/prometheus/node-exporter/textfile_collector/nginx.prom", shell=True, stdout = subprocess.PIPE,stderr = subprocess.PIPE,universal_newlines = True)
        p.wait()

        out,err = p.communicate()

        output = out.splitlines()
        for line in output:
            if line.startswith("nginx_request_count"):
                oldRequestCount = line.split()[1]
                requestCount = int(requestCount) + int(oldRequestCount)
            elif line.startswith("nginx_data_read"):
                oldDataRead = line.split()[1]
                dataRead = float(oldDataRead) + float(dataRead)
            elif line.startswith("nginx_connect_errors"):
                oldConnectionsErrors = line.split()[1]
                connectErrors = connectErrors + int(oldConnectionsErrors)
            elif line.startswith("nginx_timeout_errors"):
                oldTimeoutErrors = line.split()[1]
                timeoutErrors = timeoutErrors + int(oldTimeoutErrors)

        telemetry_output="nginx_request_count " + str(requestCount) + "\nnginx_requests_per_second " + str(reqsPerSecond) + "\nnginx_data_read " + str(dataRead) + "\nnginx_transfers_per_second " + str(transferPerSecond) + "\nnginx_p50_latency " + str(p50Latency) + "\nnginx_p75_latency " + str(p75Latency) + "\nnginx_p99_latency " + str(p99Latency) + "\nnginx_ave_latency " + str(averageLatency) + "\nnginx_connect_errors " + str(connectErrors) + "\nnginx_timeout_errors " + str(timeoutErrors) + "\n"

        #print(telemetry_output)
        with open('/var/lib/prometheus/node-exporter/textfile_collector/nginx.prom', 'w') as file:
            # Write new content to the file
            file.write(telemetry_output)
    except KeyboardInterrupt:
        print("Stopping WRK tests")
        raise SystemExit

