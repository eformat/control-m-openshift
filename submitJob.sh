#!/bin/bash

AGENT=$(oc get pods -o name -l name=controlm-agent)
AGENT=${AGENT#pod/}:
sed -i -e "s|        \"Host\" : \"controlm-agent.*\"|        \"Host\" : \"$AGENT\"|g" SampleKubeJob.json
ctm run SampleKubeJob.json