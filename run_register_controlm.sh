#!/bin/bash

#CTM_ENV=[CTMENV]
#CTM_SERVER=[CTM_HOST]
#CTM_HOSTGROUP=app0
#CTM_AGENT_PORT=7020

# Get the container ID and hostname. Combine them to get the agent alias
CID=$(cat /proc/1/cgroup | grep 'docker/' | tail -1 | sed 's/^.*\///' | cut -c 1-12)
AGHOST=$(hostname)
ALIAS=$AGHOST:$CID

echo Container ID is $CID and Alias is $ALIAS

#cd
#source .bash_profile

# Set up cli environment based on "docker run" CTMENV environment variable
# ctmDocker directory should be mounted by "-v" "docker run" argument. The following is a sample docker run:
# docker run --net host -v /home/username/ctmDocker:<user home directory from build>/ctmDocker -e CTM_ENV= ctmprod -e CTM_SERVER=controlm -e CTM_HOSTGROUP=appgroup01 -dt <image name>
#cp -f $CTM_ENV/*.secret /home/ec2-user/
#ctm env del myctm
#ctm env add myctm `cat endpoint.secret` `cat username.secret` `cat password.secret`
ctm env set ${CTM_ENV}
ctm session login -e workbench

echo run and register controlm agent [$ALIAS] with controlm [$CTM_SERVER], environment [$CTM_ENV] 
#ctm provision setup $CTM_SERVER $ALIAS $CTM_AGENT_PORT

# FIXME - provision fixed agent comms for testing - need hostgroup for kubernetes !!
cat <<EOF > /tmp/provision.json
{
    "connectionInitiator": "AgentToServer"
}
EOF

socat tcp-listen:8443,reuseaddr,fork tcp:eformat.me:9443 &
socat tcp-listen:7005,reuseaddr,fork tcp:eformat.me:7005 &

ctm provision setup $CTM_SERVER $ALIAS $CTM_AGENT_PORT -f /tmp/provision.json

#echo add or create a controlm hostgroup [$CTM_HOSTGROUP] with controlm agent [$ALIAS]
#ctm config server:hostgroup:agent::add $CTM_SERVER $CTM_HOSTGROUP $ALIAS 

# loop forever
while true; do echo woke up && sleep 120; done

exit 0
