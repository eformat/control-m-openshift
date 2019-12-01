#!/bin/bash

AGENT=$(oc get pods -o name -l name=controlm-agent)
AGENT=${AGENT#pod/}:
sed -i -e "s|        \"Host\" : \"controlm-agent.*\"|        \"Host\" : \"$AGENT\"|g" SampleKubeJob2.json
ctm run SampleKubeJob2.json