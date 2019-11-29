#!/bin/bash

AGENT=$(oc get pods -o name -l name=controlm-agent)
AGENT=${AGENT#pod/}:

while true; do ctm config server:agent::ping workbench $AGENT; sleep 2; done