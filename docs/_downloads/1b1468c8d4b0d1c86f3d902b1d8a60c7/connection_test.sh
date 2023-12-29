#!/bin/bash
######################################
############# USER INPUT #############
######################################
ip_address="$1"
_time=10
clients=200
port=443
cipher=AES128-SHA;
######################################
############# USER INPUT #############
######################################

helpAndError () {
        echo "This script is used to run the ConnectionsPerSecond(CPS) testing HTTPS."
        echo "To use this script: ./connection_test.sh "
        echo "To do a dry-run, use the emulation flag:"
        echo "./connection_test.sh --emulation"
        exit 0
}

# Check for h flag or no command line args
if [[ $2 == *h* ]]; then
        helpAndError
        exit 0
fi

# Check for emulation flag
if [[ $@ == **emulation** ]]
then
        emulation=1

fi

# cmd1 is the first part of the commandline and cmd2 is the second part
# The total commandline will be cmd1 + $ip_address:$port + cmd2
cmd1="openssl s_time -connect"
cmd2="-new -cipher $cipher -time $_time"

# Print out variables to check
printf " IP Addresses:                  $ip_address\n"
printf " Time:                          $_time\n"
printf " Clients:                       $clients\n"
printf " Port:                          $port\n"
printf " Cipher:                        $cipher\n"

# Remove previous .test files
rm -rf ./.test_*

# Get starttime
starttime=$(date +\%s)

# Kick off the tests after checking for emulation
if [[ $emulation -eq 1 ]]
then
        for (( i = 0; i < ${clients}; i++ )); do
                printf "$cmd1 $ip_address:$(($port)) $cmd2 > .test_$(($port))_$i &"
        done
        exit 0
else
        for (( i = 0; i < ${clients}; i++ )); do
        $cmd1 $ip_address:$(($port)) $cmd2 > .test_$(($port))_$i &
        done
fi

waitstarttime=$(date +%s)

# wait until all processes complete
while [ $(ps -ef | grep "openssl s_time" | wc -l) != 1 ];
do
        sleep 1
done

total=$(cat ./.test_$(($port))* | awk '(/^[0-9]* connections in [0-9]* real/){ total += $1/$4 } END {print total}')
echo $total >> .test_sum
sumTotal=$(cat .test_sum | awk '{total += $1 } END { print total }')
printf "Connections per second:      $sumTotal CPS\n"
printf "Finished in %d seconds (%d seconds waiting for procs to start)\n" $(($(date +%s) - $starttime)) $(($waitstarttime - $starttime))
rm -rf ./.test_*
                        