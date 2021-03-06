## Control-M on OpenShift

Installing BMC Control-M agent in OpenShift. Test against BMC Control-M Workbench.

Internet connectivity required (BMC agents download from aws s3).

![kube-ctrl-m](images/kube-ctrl-m.png)

High Level Architecture

```
+-----------+
| Control-M |
|   Server  |
+-----------+
      ^
comms | register
      |                        +--------+
+-----------+                  |  Kube  |--+
| Agent Pod |---- runJob.py -->|  Jobs  |  |
+-----------+                  +--------+  |
                                    +------+
```

### Installing the Control-M Workbench

See: https://docs.bmc.com/docs/automation-api/919/installation-817914518.html

Download the Control-M Workbench for Oracle VirutalBox (an OVA file).
```
wget https://s3-us-west-2.amazonaws.com/controlm-appdev/release/v9.18.3/workbench_oracle_virtual_box_ova-9.0.18.300-20190218.133426-1.ova
```

Install VirtualBox - on fedora:
```
wget -O https://download.virtualbox.org/virtualbox/rpm/fedora/virtualbox.repo /etc/yum.repos.d/virtualbox.repo
dnf -y install VirtualBox-6.0
```

Install the VirtualBox extension pack available here
```
https://www.virtualbox.org/wiki/Downloads
```

Import OVA into VirtualBox - File > Import Applicance > workbench_oracle_virtual_box_ova-9.0.18.300-20190218.133426-1.ova

After the Workbench is up and running in VirtualBox, browse to

- https://localhost:8443/automation-api/startHere.html

to get started.

Add 7705 + 7751 NAT Port-Forwarding Rules for Agent/Server communication for Testing.

### Create Container Image Locally

#### Install control-m cli

See: https://docs.bmc.com/docs/automation-api/9181/installation-784100973.html

Download and install cli:

```
wget --no-check-certificate https://localhost:8443/automation-api/ctm-cli.tgz
sudo npm -g install ctm-cli.tgz
ctm
```

#### Create CTM environment

See: 

- https://docs.bmc.com/docs/automation-api/9181/services-784100995.html#Services-TheEnvironmentService
- https://docs.bmc.com/docs/display/public/ctmapitutorials/Docker+Image+with+embedded+Control-M+Agent
- https://docs.bmc.com/docs/automation-api/918/tutorials-setting-up-the-prerequisites-783053210.html#Tutorials-Settinguptheprerequisites-set_verify

Create a CTM Environment using workbench
```
ctm environment workbench::add https://localhost:8443/automation-api
ctm environment show
ctm session login -e workbench
ctm environment set workbench
```

Create folder for this environment
```
mkdir workbench
cd workbench
echo https://localhost:8443/automation-api > endpoint.secret
echo workbench > username.secret
echo mypassword > password.secret
```

Copy contents of this folder locally (THIS HAS already been done in this repo)

```
https://github.com/eformat/automation-api-community-solutions/tree/master/3-infrastructure-as-code-examples/tutorial-docker-image-with-embedded-controlm-agent
```

#### Build container

```
make docker-build
```

Note:

For a real environment - workbench command needs replacing in `Dockerfile`
```
#RUN ctm env add ${CTMENV} `cat endpoint.secret` `cat username.secret` `cat password.secret`
RUN ctm environment workbench::add `cat endpoint.secret`
```

#### Test built container

Check name of server is `workbench`
```
$ ctm config  servers::get
[
  {
    "name": "workbench",
    "host": "localhost",
    "state": "Up",
    "message": "Connected"
  }
]
```

Run agent container locally in foreground to test it:

```
docker run --rm --net host -e CTM_ENV=workbench -e CTM_SERVER=workbench -e CTM_HOSTGROUP=appgroup01 controlm:latest
```

Successful output looks like this:

```
$ docker run --rm --net host -v ~/.kube:/home/ec2-user/.kube:z -e CTM_ENV=workbench -e CTM_SERVER=workbench -e CTM_HOSTGROUP=appgroup01 controlm:latest
Container ID is fcdb3008317b and Alias is virt:fcdb3008317b
current environment: workbench
environments: {
  "workbench": {
    "endPoint": "https://localhost:8443/automation-api",
    "user": "workbench"
  }
}
{
  "username": "workbench",
  "token": "BA3FCFBB4AEE74AA1708DCBDACB6053617FE74C1CEAB89E34AD5C30DB97A39B8659C4E2CBD7C503C61FE6A2C53D5339CDC4E555A846ABFB60AAB1871771F1070",
  "version": "9.18.3"
}
run and register controlm agent [virt:fcdb3008317b] with controlm [workbench], environment [workbench]
debug:   Locating java command
info:    Located java at:/bin/java
info:    downloading https://localhost:8443/automation-api/utils/control-m.services.provision-9.18.3.jar into /home/ec2-user/.ctm/control-m.services.provision-9.18.3.jar
info:    6MB/6MB precent: 100%
debug:   starting command: /bin/java -jar /home/ec2-user/.ctm/control-m.services.provision-9.18.3.jar -image "" -server https://localhost:8443/automation-api -action setup -environment workbench -ctms "workbench" -name "virt:fcdb3008317b" -port "7751" -cert 0 -file "/tmp/provision.json"
info:    Making SSL trust all certificates and all hostnames
info:    setting server to agent port: 7751
info:    setting agent to server port: 7005
info:    setting agent name (alias): virt:fcdb3008317b
info:    setting primary Control-M Server: localhost
info:    setting authorized Control-M Server host
info:    setting agent communication type to persistent
info:    agent configuration ended. restarting agent
info:    adding newly active agent to Control-M Server
info:    agent setup completed successfully
info:    update the agent's control modules definition
info:    exit code: 0
info:    setup succeeded
```

Run in the background
```
docker run -d --name=ctrlm-agent --net host -v ~/.kube:/home/ec2-user/.kube:z -e CTM_ENV=workbench -e CTM_SERVER=workbench -e CTM_HOSTGROUP=appgroup01 -e CTM_AGENT_PORT=7751 quay.io/eformat/controlm:latest
```

Test Locally
```
# check logs
docker logs ctrlm-agent -f

# get agent id
AGENT=virt:fcdb3008317b

# ping agent 
ctm config server:agent::ping workbench $AGENT
{
  "message": "Agent virt:fcdb3008317b is available"
}

# Run simple kube job using runJob.py (mounted local kube config should be valid)
sed -i -e "s|        \"Host\" : \"virt:.*\"|        \"Host\" : \"$AGENT\"|g" SampleKubeJob.json

# runs job in default namespace
ctm run SampleKubeJob.json
```

#### Push image to your registry

```
make docker-push
```

## OpenShift

As `cluser-admin` user

### Permissions for CTRL-M Agent

Setup cluster role for service account that will be used by `DemonSet`

```
oc create -f - <<EOF
apiVersion: v1
kind: Project
metadata:
  labels:
    app: controlm-agent
  name: controlm-agent
  annotations:
    # openshift.io/node-selector: ''
    openshift.io/description: 'Control-M Agent'
    openshift.io/display-name: 'Control-M Agent'
EOF

oc create -f - <<EOF
apiVersion: rbac.authorization.k8s.io/v1
kind: ClusterRole
metadata:
  name: controlm-agent
  namespace: controlm-agent
rules:
  - apiGroups: ["", "batch", "extensions", "apps"]
    resources: ["*"]
    verbs: ["*"]
EOF

oc create -f - <<EOF
kind: ServiceAccount
apiVersion: v1
metadata:
  name: controlm-agent
  namespace: controlm-agent
EOF

oc create -f - <<EOF
apiVersion: authorization.openshift.io/v1
kind: ClusterRoleBinding
metadata:
  name: controlm-agent
roleRef:
  name: controlm-agent
subjects:
  - kind: ServiceAccount
    name: controlm-agent
    namespace: controlm-agent
EOF
```

```
oc adm policy add-scc-to-user privileged -z controlm-agent -n controlm-agent
```

### Label Nodes for DameonSet

```
# all nodes in cluster
oc label nodes --all controlm=true
# single node for testing
oc label node ip-10-0-169-219.ap-southeast-1.compute.internal controlm=true
```

### Create DaemonSet

```
oc apply -f daemonSet.yaml
```

OR
```
oc create -f - <<EOF
apiVersion: extensions/v1beta1
kind: DaemonSet
metadata:
  name: controlm-agent
  namespace: controlm-agent
spec:
  template:
    metadata:
      labels:
        name: controlm-agent
    spec:
      affinity:
        nodeAffinity:
          requiredDuringSchedulingIgnoredDuringExecution:
            nodeSelectorTerms:
            - matchExpressions:
              - key: controlm
                operator: Exists
      serviceAccount: controlm-agent
      serivceAccountName: controlm-agent
      securityContext:
        privileged: true
      containers:
      - name: ctmagent-container
        securityContext:
          privileged: true
        ports:
        - containerPort: 7750
          name: "ctm"
          protocol: TCP
        env:
        - name: CTM_ENV
          value: "workbench"
        - name: CTM_SERVER
          value: "workbench"
        - name: CTM_HOSTGROUP
          value: "appgroup01"
        - name: CTM_AGENT_PORT
          value: "7750"
        image: quay.io/eformat/controlm:latest
        imagePullPolicy: Always
        terminationGracePeriodSeconds: 30
EOF
```

### Remote Port Forward and socat magic

My original plan was to `virt-v2v` the OVA and run the Control-M Workbench image on OpenShift using `kube-virt`. The conversion failed :(

So, because the control-m agent is configured to connect to the workbench running on localhost:

```
---------------------------------                               ----------------------------      -------------------------
| Ctr-M OVA (running on laptop) | --- (ssh RemoteForward) --->  | Internet Accessible Host | <--- | Pod (control-m agent) |
---------------------------------                               ----------------------------      -------------------------
```

ssh/config
```
	RemoteForward :10443 0.0.0.0:8443
	RemoteForward :10751 0.0.0.0:7751
	RemoteForward :10005 0.0.0.0:7005
```
internet accessible host
```
sudo iptables -A INPUT -p tcp -m state --state NEW -m tcp --dport 9443 -j ACCEPT
sudo iptables -A INPUT -p tcp -m state --state NEW -m tcp --dport 7751 -j ACCEPT
sudo iptables -A INPUT -p tcp -m state --state NEW -m tcp --dport 7005 -j ACCEPT
socat tcp-listen:9443,reuseaddr,fork tcp:localhost:10443 &
socat tcp-listen:7751,reuseaddr,fork tcp:localhost:10751 &
socat tcp-listen:7005,reuseaddr,fork tcp:localhost:10005 &
```
control-m pod
```
oc rsh $(oc get pods -o name -l name=controlm-agent)
socat tcp-listen:8443,reuseaddr,fork tcp:host.me:9443 &
socat tcp-listen:7005,reuseaddr,fork tcp:host.me:7005 &
```

Test
```
oc rsh $(oc get pods -o name -l name=controlm-agent)
sh-4.2$ ctm session login -e workbench
{
  "username": "workbench",
  "token": "E579435F74A1A38E8C0FE9A1C45CBA410CB7299E798EFD068A16842ACB101CD82CEB00CB4B56FA4557C585238CEE35A1E4EF27F02C64FD00A26A29817FAEB0AC",
  "version": "9.18.3"
}
```

### OpenShift manual provision

In agent pod
```
oc rsh $(oc get pods -o name -l name=controlm-agent)

CID=$(cat /proc/1/cgroup | grep 'docker/' | tail -1 | sed 's/^.*\///' | cut -c 1-12)
AGHOST=$(hostname)
ALIAS=$AGHOST:$CID
CTM_SERVER=workbench
CTM_HOSTGROUP=appgroup01
CTM_AGENT_PORT=7751

cat <<EOF > /tmp/provision.json
{
    "connectionInitiator": "AgentToServer"
}
EOF

socat tcp-listen:8443,reuseaddr,fork tcp:host.me:9443 &
socat tcp-listen:7005,reuseaddr,fork tcp:host.me:7005 &

ctm provision setup $CTM_SERVER $ALIAS $CTM_AGENT_PORT -f /tmp/provision.json
```

From laptop:
```
AGENT=$(oc get pods -o name -l name=controlm-agent)
AGENT=${AGENT#pod/}:

ctm session login -e workbench
ctm config server:agent::ping workbench $AGENT

sed -i -e "s|        \"Host\" : \"controlm-agent.*\"|        \"Host\" : \"$AGENT\"|g" SampleKubeJob.json
ctm run SampleKubeJob.json

# useful commands
ctm config server:agent::delete workbench $AGENT
while true; do ctm config server:agent::ping workbench $AGENT; sleep 2; done
ctm config server:hostgroups::get workbench
ctm config server:agents::get workbench

# useful scripts
./watchAgent.sh
./submitJob.sh
```

### Links

- https://jobsascode.io/control-m-and-kubernetes/
- http://jobsascode.io/control-m-agent-configuration-as-a-daemonset-for-kubernetes/
- https://jobsascode.io/docker-image-with-embedded-control-m-agent/
- https://docs.bmc.com/docs/automation-api/919/installation-817914518.html
- https://docs.bmc.com/docs/automation-api/9181/installation-784100973.html
- https://docs.bmc.com/docs/automation-api/9181/services-784100995.html#Services-TheEnvironmentService
- https://docs.bmc.com/docs/display/public/ctmapitutorials/Docker+Image+with+embedded+Control-M+Agent
- https://docs.bmc.com/docs/automation-api/918/tutorials-setting-up-the-prerequisites-783053210.html#Tutorials-Settinguptheprerequisites-set_verify
- https://www.redhat.com/en/blog/importing-vms-kvm-virt-v2v
- https://www.youtube.com/watch?v=i8AHRaUN0GA