#!/bin/sh

loopctr=${LOOPCTR:-3};
stime=${STIME:-2};
xcode=${XCODE:-0};

name=${1:-World};
ip=`ip addr show eth0 | grep "inet\b" | awk '{print $2}' | cut -d/ -f1`
while [ ${loopctr} -gt 0 ]; do echo "Welcome from ${HOSTNAME}:${ip}"; loopctr=$((loopctr-1)); sleep ${stime}; done
exit ${xcode}
