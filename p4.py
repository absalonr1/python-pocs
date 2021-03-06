from urlmatch import urlmatch

from asyncore import write
import subprocess
import re
import sys

# python3 -m pip install requests
import requests
#import json

def trimAndRemoveDoubleQuotes(string):
    string=string.replace("\"","")
    string=string.replace("\n","")
    return string

def downloadJson(url, filename):
    req = requests.get(url)
    serviceFileTemp = filename+".temp.json"
    with open(serviceFileTemp, 'wb') as fd:
        for chunk in req.iter_content(chunk_size=128):
            fd.write(chunk)
    subPrc = subprocess.Popen(['jq . '+serviceFileTemp+' > '+filename ], shell=True) 
    subPrc.communicate()
    subPrc = subprocess.Popen(['rm '+serviceFileTemp ], shell=True) 
    subPrc.communicate()


def getK8sDeployName(k8sNameSpace, selectorApp):
    subPrc = subprocess.Popen([
                                  'kubectl get deploy -n ' + k8sNameSpace + ' -o json | jq \'.items[] | select(.spec.template.metadata.labels.app == "' + selectorApp + '" )\' | jq \'.metadata.name\' '],
                              shell=True, stdout=subprocess.PIPE)
    k8sDeployName = str(subPrc.communicate()[0].decode("utf-8"))
    k8sDeployName = trimAndRemoveDoubleQuotes(k8sDeployName)
    print("K8S-deployName: " + k8sDeployName)
    return k8sDeployName


def getK8sSvcSelectorApp(k8sNameSpace, k8sSvcName, selectorApp):
    if (len(k8sSvcName) > 0 and len(k8sNameSpace) > 0):
        subPrc = subprocess.Popen(
            ['kubectl get svc ' + k8sSvcName + ' -n ' + k8sNameSpace + ' -o json | jq \'.spec.selector.app\''],
            shell=True, stdout=subprocess.PIPE)
        selectorApp = str(subPrc.communicate()[0].decode("utf-8"))
        selectorApp = trimAndRemoveDoubleQuotes(selectorApp)
    print("K8S-selectorApp: " + selectorApp)
    return selectorApp


def getIngressNameSpace(ingressFileName, k8sNameSpace, k8sSvcName):
    subPrc = subprocess.Popen(
        ['jq \'.items[] | select ( .spec.rules[].http.paths[].backend.service.name == "' + k8sSvcName +
         '")\' ' + ingressFileName + ' | jq \'.metadata.namespace\''], shell=True, stdout=subprocess.PIPE)
    k8sNameSpace = str(subPrc.communicate()[0].decode("utf-8"))
    k8sNameSpace.replace("\"", "")
    if (k8sNameSpace.find("\n")):
        k8sNameSpace = k8sNameSpace.split("\n")
        k8sNameSpace = trimAndRemoveDoubleQuotes(k8sNameSpace[0])
    print("K8S-Namespace: " + k8sNameSpace)
    return k8sNameSpace

albDicc = dict()

def getK8sSvcName(albDNS,ingressFile,svcUpPath):
    k8sSvcName = ""
    dicc_text = ""
    #TODO: jq -r '.items[] | select ( .status.loadBalancer.ingress[]?.hostname == "internal-k8s-ingrztmsuniversal-479f7c3508-1353133394.us-west-2.elb.amazonaws.com" )' k8s-ingress-dev.json | jq '.spec.rules[].http.paths[0].backend.service.name +","+ .spec.rules[].http.paths[0].path +","+ .metadata.name'

    command = 'jq \'.items[] | select ( .status.loadBalancer.ingress[]?.hostname == "' + albDNS + '" )\' '+ingressFile+' | jq \'.spec.rules[].http.paths[0].backend.service.name , .spec.rules[].http.paths[0].path\''
    # print(command)
    subPrc = subprocess.Popen([command], shell=True, stdout=subprocess.PIPE)
    temp1 = str(subPrc.communicate()[0].decode("utf-8"))
    arr = temp1.split("\n")
    arr = arr[0:len(arr) - 1]
    
    """
    albDicc:
        DNS1
         |__ path1:srv-name1
         |__ path2:srv-name2
        DNS2
         |__ path3:srv-name3
         |__ path4:srv-name4
    """


    if (len(arr) > 0):

        if (albDicc.get(albDNS) == None and len(arr) > 0):
            albDicc[albDNS] = dict()
            counter = 0
            while True:
                albDicc[albDNS][
                    trimAndRemoveDoubleQuotes(arr[counter + 1])] = trimAndRemoveDoubleQuotes(
                    arr[counter])
                counter = counter + 2
                if (counter >= len(arr)):
                    break
        # print(albDicc)

        match = False
        
        dicc_text = str(albDicc[albDNS])
        dicc_text = dicc_text.replace(",", ";")
        for k in albDicc[albDNS].keys():
            match_pattern = 'http://host' + k
            match = urlmatch(match_pattern, 'http://host' + svcUpPath)
            print(match_pattern + " | " + "http://host" + svcUpPath + "-->" + str(match))
            if (not match and not svcUpPath.endswith("/")):
                temp_svcUpPath = svcUpPath + "/"
                match = urlmatch(match_pattern, 'http://host' + temp_svcUpPath)
                print(match_pattern + " | " + "http://host" + temp_svcUpPath + "-->" + str(match))
            if (match):
                print("Found!! service name: " + albDicc[albDNS][k])
                k8sSvcName = albDicc[albDNS][k]
                break
    return k8sSvcName,dicc_text


def getKongSvcHost(servicesFileName, svcId):
    subPrc = subprocess.Popen(
        ['jq \'.data[] | select (.id == "' + svcId + '" )\' ' + servicesFileName + ' | jq \'.host\' '], shell=True,
        stdout=subprocess.PIPE)
    albDNS = str(subPrc.communicate()[0].decode("utf-8"))
    albDNS = trimAndRemoveDoubleQuotes(albDNS)
    print("ALB DNS: " + albDNS)
    return albDNS


def getKongSvcPlugins(svcId, svcPlugins):
    req = requests.get('http://' + host_port_kong + '/services/' + svcId + '/plugins')
    jsonRespDictionary = req.json()
    flagLambda = False
    # print(jsonRespDictionary)
    if (len(jsonRespDictionary) > 0):
        for item in jsonRespDictionary["data"]:
            plugId=item["id"]
            svcPlugins = svcPlugins + "/" + item["name"]
            if (svcPlugins.find("lambda") != -1):
                flagLambda = True
            if (item["name"] == "cors"):
                svcPlugins = svcPlugins + "(" + str(item["config"]["methods"]).replace(',', ' - ') + ")" + "(" + str(
                    item["config"]["origins"]).replace(',', ' - ') + ")"
            if (item["name"] == "jwt-keycloak"):
                req = requests.get('http://' + host_port_kong + '/plugins/' + plugId )
                plugDictionary = req.json()
                svcPlugins = svcPlugins + " (" + str(plugDictionary["config"]["allowed_iss"]).replace(',', ' - ') + ")" 
                # print("allowed_iss:")
                # for iss in plugDictionary["config"]["allowed_iss"]:
                #     print(iss)
    print("Kong service plugins: " + svcPlugins)
    return flagLambda, svcPlugins


def getKongSvcUpPath(servicesFileName, svcId):
    subPrc = subprocess.Popen(['jq \'.data[] | select (.id == "' + svcId + '" ) \' ' + servicesFileName + ' | jq \'.path\' '],
                                shell=True, stdout=subprocess.PIPE)
    svcUpPath = str(subPrc.communicate()[0].decode("utf-8"))
    svcUpPath = trimAndRemoveDoubleQuotes(svcUpPath)

    return svcUpPath


def getKongSvcName(servicesFileNames, svcId):
    for servicesFileName in servicesFileNames:
        subPrc = subprocess.Popen(
            ['jq \'.data[] | select (.id == "' + svcId + '" )\' ' + servicesFileName + ' | jq \'.name\' '], shell=True,
            stdout=subprocess.PIPE)
        svcName = str(subPrc.communicate()[0].decode("utf-8"))
        svcName = trimAndRemoveDoubleQuotes(svcName)
        if (len(svcName) > 0):
            print("Service NAME: " + svcName)
            break
    return servicesFileName, svcName


def kongSvcId(routeId, routesFileName):
    subPrc = subprocess.Popen(
        ['jq \'.data[] | select(.id == "' + routeId + '")\' ' + routesFileName + ' | jq \'.service.id\''], shell=True,
        stdout=subprocess.PIPE)
    svcId = str(subPrc.communicate()[0].decode("utf-8"))
    svcId = trimAndRemoveDoubleQuotes(svcId)
    print("Service ID: " + svcId)
    return svcId


def kongRoutePath(routeId, routesFileName):
    subPrc = subprocess.Popen(
        ['jq \'.data[] | select(.id == "' + routeId + '")\' ' + routesFileName + ' | jq \'.paths[]\''], shell=True,
        stdout=subprocess.PIPE)
    path = str(subPrc.communicate()[0].decode("utf-8"))
    path = trimAndRemoveDoubleQuotes(path)
    # todo:  puede ser un array ...
    print("Route Path[]: " + path)
    return path


def genCSV(routesFileNames, servicesFileNames, ingressFileName):
    albDicc = dict()

    myFile.write("Route ID" + csvSeparator)
    myFile.write("Route path" + csvSeparator)
    myFile.write("svcName" + csvSeparator)
    myFile.write("svcId" + csvSeparator)
    myFile.write("svc upstream path" + csvSeparator)
    myFile.write("svcPlugins" + csvSeparator)
    myFile.write("albDNS" + csvSeparator)
    myFile.write("k8sSvcName" + csvSeparator)
    myFile.write("k8sNameSpace" + csvSeparator)
    myFile.write("selectorApp" + csvSeparator)
    myFile.write("k8sDeployName" + csvSeparator)
    myFile.write("dicc_text\n")

    for routesFileName in routesFileNames:
        print(routesFileName)

        subPrc = subprocess.Popen(['jq', '(.data[].id)', routesFileName], stdout=subprocess.PIPE)
        routeIdArray = str(subPrc.communicate()[0].decode("utf-8"))
        routeIdArray = routeIdArray.split('\n')

        for routeId in routeIdArray:
            if (len(routeId) == 0):
                continue

            routeId = trimAndRemoveDoubleQuotes(routeId)

            if (routeId != "a9cae54e-0518-4f7c-930f-2454c09e366a"):
                pass
            path = ""
            svcId = ""
            svcUpPath = ""
            svcPlugins = ""
            albDNS = ""
            svcName = ""
            k8sSvcName = ""
            k8sNameSpace = ""
            selectorApp = ""
            k8sDeployName = ""
            dicc_text = ""

            path = kongRoutePath(routeId, routesFileName)

            svcId = kongSvcId(routeId, routesFileName)

            servicesFileName,svcName = getKongSvcName(servicesFileNames, svcId)

            assert (len(svcName) > 0)

            svcUpPath = getKongSvcUpPath(servicesFileName, svcId)

            assert (len(servicesFileName) > 0)

            flagLambda, svcPlugins = getKongSvcPlugins(svcId, svcPlugins)

            if (not flagLambda):
                albDNS = getKongSvcHost(servicesFileName, svcId)

                # no es una IP?
                if (re.match("[0-9]+\.[0-9]+\.[0-9]+\.[0-9]+", albDNS) is None and albDNS.endswith("amazonaws.com")):

                    k8sSvcName, dicc_text = getK8sSvcName(albDNS, ingressFileName,svcUpPath)

                    if (len(k8sSvcName) > 0):

                        k8sNameSpace = getIngressNameSpace(ingressFileName, k8sNameSpace, k8sSvcName)

                        selectorApp = getK8sSvcSelectorApp(k8sNameSpace, k8sSvcName, selectorApp)

                        if (len(selectorApp) > 0):
                            k8sDeployName = getK8sDeployName(k8sNameSpace, selectorApp)

            myFile.write((routeId) + csvSeparator)
            myFile.write((path) + csvSeparator)
            myFile.write((svcName) + csvSeparator)
            myFile.write((svcId) + csvSeparator)
            myFile.write((svcUpPath) + csvSeparator)
            myFile.write((svcPlugins) + csvSeparator)
            myFile.write((albDNS) + csvSeparator)
            myFile.write((k8sSvcName) + csvSeparator)
            myFile.write((k8sNameSpace) + csvSeparator)
            myFile.write((selectorApp) + csvSeparator)
            myFile.write((k8sDeployName) + csvSeparator)
            myFile.write((dicc_text))
            myFile.write("\n")

            path = ""
            routeId = ""
            kongSvcName = ""
            svcId = ""
            svcUpPath = ""
            svcPlugins = ""
            albDNS = ""
            svcName = ""
            k8sSvcName = ""
            k8sNameSpace = ""
            selectorApp = ""
            dicc_text = ""

    myFile.close()

env_suffix="dev"
if(len(sys.argv)>1):
    if(sys.argv[1] == "prod"):
        env_suffix="prod"
    elif(sys.argv[1] == "qa"):
        env_suffix="qa"
    elif(sys.argv[1] == "dev"):
        env_suffix="dev"

env_suffix="dev"
if(len(sys.argv)>1):
    if(sys.argv[1] == "prod"):
        env_suffix="prod"
    elif(sys.argv[1] == "qa"):
        env_suffix="qa"
    elif(sys.argv[1] == "dev"):
        env_suffix="dev"

host_port_kong = "localhost:8001"

if(len(sys.argv)>1):
    if(not (sys.argv[1] == "prod" or sys.argv[1] == "qa" or sys.argv[1] == "dev")):
        print("Parmetro debe ser [prod|qa|dev]")
        quit()


bufsize = 1
myFile = open('summary_'+env_suffix+'.csv', 'w', buffering=bufsize)
csvSeparator = ","


#  Descargar json de servicios kong


serviceFile1 = "kong-services-"+env_suffix+".json"
serviceFile2 = "kong-services-next-"+env_suffix+".json"
ingressFile = "k8s-ingress-"+env_suffix+".json"
routeFile1 = "kong-routes-"+env_suffix+".json"
routeFile2 = "kong-routes-next-"+env_suffix+".json"

routesFileNames = [routeFile1,routeFile2]
servicesFileNames = [serviceFile1,serviceFile2]

url = "http://"+host_port_kong+"/services"
downloadJson(url,serviceFile1)
subPrc = subprocess.Popen(['jq','.next',serviceFile1] , stdout = subprocess.PIPE) 
nextToken = str(subPrc.communicate()[0].decode("utf-8"))
nextToken=nextToken.lstrip().rstrip()
nextToken=nextToken[1:len(nextToken)-1]
print(nextToken)

if(len(nextToken)>10):
    downloadJson("http://"+host_port_kong+nextToken, serviceFile2)
else:
    servicesFileNames=servicesFileNames[0:1]

# #  Descargar json de routes kong



url = "http://"+host_port_kong+"/routes"
downloadJson(url,routeFile1)
subPrc = subprocess.Popen(['jq','.next',routeFile1] , stdout = subprocess.PIPE) 
nextToken = str(subPrc.communicate()[0].decode("utf-8"))
nextToken=nextToken.lstrip().rstrip()
nextToken=nextToken[1:len(nextToken)-1]
print(nextToken)

if(len(nextToken)>10):
    downloadJson("http://"+host_port_kong+nextToken, routeFile2)
else:
    routesFileNames=routesFileNames[0:1]

# #Descargar json de ingress
k8sProd="kubectl config use-context arn:aws:eks:us-east-1:772932014686:cluster/eksprod01 && export AWS_PROFILE=default"
k8sDesa="kubectl config use-context arn:aws:eks:us-west-2:311028179126:cluster/ekslab06 && export AWS_PROFILE=bx-dev"
k8sQa="kubectl config use-context arn:aws:eks:us-east-1:598597004437:cluster/eksqa012 && export AWS_PROFILE=bx-qa"

clusterConf=k8sDesa
if(len(sys.argv)>1):
    if(sys.argv[1] == "prod"):
        clusterConf=k8sProd
    elif(sys.argv[1] == "qa"):
        clusterConf=k8sQa
    elif(sys.argv[1] == "dev"):
        clusterConf=k8sDesa

subPrc = subprocess.Popen([clusterConf] , shell=True,stdout = subprocess.PIPE) 
out = str(subPrc.communicate()[0].decode("utf-8"))
print(out)
subPrc = subprocess.Popen(['kubectl get ingress -A -o json > '+ingressFile] , shell=True, stdout = subprocess.PIPE) 
out = str(subPrc.communicate()[0].decode("utf-8"))
print(out)


# generar Excel
genCSV(ingressFileName=ingressFile, routesFileNames=routesFileNames,servicesFileNames=servicesFileNames)


# https://stackoverflow.com/questions/7353054/running-a-command-line-containing-pipes-and-displaying-result-to-stdout