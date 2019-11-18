
from os import path
from kubernetes import client, config, utils

import getopt, os, sys, time
import signal

import urllib3
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

kNameSpace = "default"
stime = 15				# Default sleep interval for status check

def main(argv):
   global kJobname, kNameSpace, podName
   kJobname = ''
   kNameSpace = ''
   outputfile = ''
   try:
     opts, args = getopt.getopt(argv,"hj:n:",["jname=", "namespace="])
   except getopt.GetoptError:
     print("runjob.py -j <jobname>")
     sys.exit(2)
   for opt, arg in opts:
     if opt == '-h':
        print("runjob.py -j <jobname>")
        sys.exit()
     elif opt in ("-j", "--jname"):
        kJobname = arg
     elif opt in ("-n", "--namespace"):
        kNameSpace = arg

   print("Processing job: " + kJobname + " namespace: " + kNameSpace)
   startJob(kJobname, kNameSpace)
   
   signal.signal(signal.SIGTERM, termSignal)
   
   jobStatus = status(kJobname, kNameSpace)
   
   podName = listPod(kJobname, kNameSpace)
   getLog(podName, kNameSpace)
      
   deleteJob(kJobname, podName, kNameSpace)
   
   quit(0)
   
def startJob(kJobname, kNameSpace):
   yaml = kJobname + ".yaml"
   try:
      config.load_incluster_config()
   except:
      config.load_kube_config('.kube/config')
   k8s_client = client.ApiClient()
   k8s_api = utils.create_from_yaml(k8s_client, yaml)
   k8s_batch_api = client.BatchV1Api(None)
   
   try:
     kJob = k8s_batch_api.read_namespaced_job(kJobname, kNameSpace)
   except:
     print("Failed creating job: " + kJobname)
     sys.exit(2)
	  
   print("Job {0} created".format(kJob.metadata.name))
   return
   
def status(kJobname, kNameSpace):
   jobStatus = "Success"
   jobRunning = "Running"
   podLabelSelector = 'job-name=' + kJobname
   try:
      config.load_incluster_config()
   except:
      config.load_kube_config('.kube/config')
   batchV1 = client.BatchV1Api()
   time.sleep(5)                  # Give the Pod a chance to initialize
   
   while jobRunning == "Running":
      try:
         ret = batchV1.list_namespaced_job(kNameSpace, label_selector=podLabelSelector)
      except:
         print("Failed getting job status: " + kJobname)
         sys.exit(4)
		 
      for i in ret.items:
         jobStatus = str(i.status.active)
         print("Kubernetes Job Status :" + jobStatus)
      if jobStatus == "1":
         jobRunning = "Running"
         time.sleep(stime)
      else:
         jobRunning = "Not Running"
	  
   print("Job ended execution")
   return jobStatus
   
def listPod(kJobname, kNameSpace):
   try:
      config.load_incluster_config()
   except:
      config.load_kube_config('.kube/config')
   coreV1 = client.CoreV1Api()
   podLabelSelector = 'job-name=' + kJobname
   print("Listing pod for jobname:" + kJobname)
   ret = coreV1.list_namespaced_pod(kNameSpace, label_selector=podLabelSelector)
   for i in ret.items:
      podName = str(i.metadata.name)
      print("%s" %
          (i.metadata.name))
   return podName

  
def getLog(podName, kNameSpace):
   try:
      config.load_incluster_config()
   except:
      config.load_kube_config('.kube/config')
   coreV1 = client.CoreV1Api()
   ret = coreV1.read_namespaced_pod_log(podName, kNameSpace)
   print("Log output from Pod: " + podName)
   print(ret)
   return
   
def deleteJob(kJobname, podName, kNameSpace):
   try:
      config.load_incluster_config()
   except:
      config.load_kube_config('.kube/config')
   jobBody = client.V1Job()
   batchV1 = client.BatchV1Api()
   ret = batchV1.delete_namespaced_job(kJobname, kNameSpace)
   print("Job deleted: " + kJobname)
   
   podBody = client.V1DeleteOptions()
   coreV1 = client.CoreV1Api()
   ret = coreV1.delete_namespaced_pod(podName, kNameSpace)
   print("Pod deleted: " + podName)
   
   return

def termSignal(signalNumber, frame):  
   global kJobname, kNameSpace, podName
   print("Terminating due to SIGTERM: %i" % signalNumber)
   podName = listPod(kJobname)
   getLog(podName)
   deleteJob(kJobname, podName)
   sys.exit(8)
   
if __name__ == '__main__':
   main(sys.argv[1:])
