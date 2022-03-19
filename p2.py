from urlmatch import urlmatch

from asyncore import write
import subprocess
import re

# python3 -m pip install requests
import requests
#import json

def trimAndRemoveDoubleQuotes(string):
    string=string.replace("\"","")
    string=string.replace("\n","")
    return string

# alb= "internal-k8s-ingresscontainer-fcc9610877-445198957.us-west-2.elb.amazonaws.com"
# routePath = "/api/container/acklink/v1"
# command = 'jq \'.items[] | select ( .status.loadBalancer.ingress[].hostname == "internal-k8s-ingresscontainer-fcc9610877-445198957.us-west-2.elb.amazonaws.com" )\' k8s-ingress.json | jq \'.spec.rules[].http.paths[0].backend.service.name , .spec.rules[].http.paths[0].path\''
# #print(command)
# subPrc = subprocess.Popen([command], shell=True, stdout = subprocess.PIPE)
# k8sSvcName = str(subPrc.communicate()[0].decode("utf-8"))
# arr = k8sSvcName.split("\n")
# arr = arr[0:len(arr)-1]
# #print(len(arr))

# albDicc = dict()


# if(albDicc.get(alb)== None and len(arr)>0):
#     albDicc[alb] = dict()
#     counter = 0
#     while True:
#         albDicc[alb][trimAndRemoveDoubleQuotes(arr[counter+1])] = trimAndRemoveDoubleQuotes(arr[counter])
#         counter=counter+2
#         if(counter>=len(arr)):
#             break
# #print(albDicc)


# for k in albDicc[alb].keys():
#     match_pattern = 'http://host'+k
#     match = urlmatch(match_pattern, 'http://host'+routePath)
#     print(match_pattern + " | " + "http://host" + routePath+"-->"+str(match))
#     if(not match and not routePath.endswith("/")):
#         tempRoutePath=routePath+"/"
#         match = urlmatch(match_pattern, 'http://host'+tempRoutePath)
#         print(match_pattern + " | " + "http://host" + tempRoutePath+"-->"+str(match))
#     if(match):
#         print("Found!! service name: "+albDicc[alb][k])
#         break
#     print("--")





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



bufsize = 1
myFile = open('summary.csv', 'w', buffering=bufsize)
csvSeparator = ","

def genCSV(routesFileNames,servicesFileNames, ingressFileName):
    albDicc = dict()

    myFile.write("Route ID"+csvSeparator)
    myFile.write("Route path"+csvSeparator)
    myFile.write("svcName"+csvSeparator)
    myFile.write("svcId"+csvSeparator)
    myFile.write("svc upstream path"+csvSeparator)
    myFile.write("svcPlugins"+csvSeparator)
    myFile.write("albDNS"+csvSeparator)
    myFile.write("k8sSvcName"+csvSeparator)
    myFile.write("k8sNameSpace"+csvSeparator)
    myFile.write("selectorApp"+csvSeparator)
    myFile.write("k8sDeployName"+csvSeparator)
    myFile.write("dicc_text\n")
    
    for routesFileName in routesFileNames:
        print(routesFileName)

        subPrc = subprocess.Popen(['jq','(.data[].id)',routesFileName], stdout = subprocess.PIPE) 
        routeIdArray = str(subPrc.communicate()[0].decode("utf-8"))
        routeIdArray = routeIdArray.split('\n')
        
        for routeId in routeIdArray:
            if(len(routeId)==0):
                continue
            
            routeId=trimAndRemoveDoubleQuotes(routeId)
            
            if(routeId != "2663a1d5-ba83-4125-abfd-591fd96f83e5"):
                continue
            path=""
            svcId=""
            svcUpPath=""
            svcPlugins=""
            albDNS=""
            svcName=""
            k8sSvcName=""
            k8sNameSpace=""
            selectorApp=""
            k8sDeployName=""     
            dicc_text="" 
        
            

            if(routeId=="0d09efb7-2be6-48ec-85ae-3f9f5d0531e3"):
                print("1")
            #---------------------------
            # Busca route PATH
            #---------------------------

            subPrc = subprocess.Popen(['jq \'.data[] | select(.id == "'+routeId+'")\' '+routesFileName+' | jq \'.paths[]\''], shell=True, stdout = subprocess.PIPE) 
            path = str(subPrc.communicate()[0].decode("utf-8"))
            path=trimAndRemoveDoubleQuotes(path)
            # todo:  puede ser un array ...
            print("Route Path[]: "+ path)
                
            #---------------------------
            # Busca kong service ID
            #---------------------------
            subPrc = subprocess.Popen(['jq \'.data[] | select(.id == "'+routeId+'")\' '+routesFileName+' | jq \'.service.id\''], shell=True, stdout = subprocess.PIPE)
            svcId = str(subPrc.communicate()[0].decode("utf-8"))
            svcId=trimAndRemoveDoubleQuotes(svcId)
            print("Service ID: "+ svcId)

            

            #---------------------------
            # Busca kong service name
            #---------------------------
            for servicesFileName in servicesFileNames:
                subPrc = subprocess.Popen(['jq \'.data[] | select (.id == "'+svcId+'" )\' '+servicesFileName+' | jq \'.name\' '],shell=True, stdout = subprocess.PIPE) 
                svcName = str(subPrc.communicate()[0].decode("utf-8"))
                svcName = trimAndRemoveDoubleQuotes(svcName)
                if(len(svcName)>0):
                    print("Service NAME: "+ svcName)
                    break

            assert(len(svcName)>0)
            #---------------------------------
            # Busca kong service upstream path
            #---------------------------------
            for servicesFileName in servicesFileNames:
                subPrc = subprocess.Popen(['jq \'.data[] | select (.id == "'+svcId+'" ) \' '+servicesFileName+' | jq \'.path\' '], shell=True, stdout = subprocess.PIPE) 
                svcUpPath = str(subPrc.communicate()[0].decode("utf-8"))
                svcUpPath =trimAndRemoveDoubleQuotes(svcUpPath)
                if(len(svcUpPath)>0):
                    print("Service Upstream PATH: "+ svcUpPath)
                    break

            
            
            # Identificar los plugins asociados al service
            req = requests.get('http://'+host_port_kong+'/services/'+svcId+'/plugins')
            jsonRespDictionary = req.json()
            flagLambda = False
            #print(jsonRespDictionary)
            if(len(jsonRespDictionary)>0):
                for item in jsonRespDictionary["data"]:
                    svcPlugins= svcPlugins+"/"+item["name"]
                    if(svcPlugins.find("lambda") != -1):
                        flagLambda = True
                    if(item["name"]=="cors"):
                        svcPlugins=svcPlugins+"("+str(item["config"]["methods"]).replace(',',' - ')+")"+"("+str(item["config"]["origins"]).replace(',',' - ')+")"
                        
                        
            print("Kong service plugins: "+svcPlugins)

            

            if(not flagLambda):
                subPrc = subprocess.Popen(['jq \'.data[] | select (.id == "'+svcId+'" )\' '+servicesFileName+' | jq \'.host\' '], shell=True, stdout = subprocess.PIPE) 
                albDNS = str(subPrc.communicate()[0].decode("utf-8"))
                albDNS = trimAndRemoveDoubleQuotes(albDNS)
                print("ALB DNS: "+ albDNS)
                
               

                # no es una IP?
                if(re.match("[0-9]+\.[0-9]+\.[0-9]+\.[0-9]+",albDNS) is None and albDNS.endswith("amazonaws.com")):

                    #---------------------------------
                    # Busca k8s svc name
                    #---------------------------------

                    
                    routePath = path
                    command = 'jq \'.items[] | select ( .status.loadBalancer.ingress[].hostname == "'+albDNS+'" )\' k8s-ingress.json | jq \'.spec.rules[].http.paths[0].backend.service.name , .spec.rules[].http.paths[0].path\''
                    #print(command)
                    subPrc = subprocess.Popen([command], shell=True, stdout = subprocess.PIPE)
                    temp1 = str(subPrc.communicate()[0].decode("utf-8"))
                    arr = temp1.split("\n")
                    arr = arr[0:len(arr)-1]

                    if(len(arr)>0):

                        if(albDicc.get(albDNS)== None and len(arr)>0):
                            albDicc[albDNS] = dict()
                            counter = 0
                            while True:
                                albDicc[albDNS][trimAndRemoveDoubleQuotes(arr[counter+1])] = trimAndRemoveDoubleQuotes(arr[counter])
                                counter=counter+2
                                if(counter>=len(arr)):
                                    break
                        #print(albDicc)

                        match = False
                        k8sSvcName="non match"
                        dicc_text=str(albDicc[albDNS])
                        dicc_text=dicc_text.replace(",",";")
                        for k in albDicc[albDNS].keys():
                            match_pattern = 'http://host'+k
                            match = urlmatch(match_pattern, 'http://host'+routePath)
                            #print(match_pattern + " | " + "http://host" + routePath+"-->"+str(match))
                            if(not match and not routePath.endswith("/")):
                                tempRoutePath=routePath+"/"
                                match = urlmatch(match_pattern, 'http://host'+tempRoutePath)
                                #print(match_pattern + " | " + "http://host" + tempRoutePath+"-->"+str(match))
                            if(match):
                                print("Found!! service name: "+albDicc[albDNS][k])
                                k8sSvcName=albDicc[albDNS][k]
                                break

                        #assert(match)
                        if(match):
                            #----------------------------------------------
                            # Busca k8s svc nameSpace asociado al ingress
                            #----------------------------------------------
                            subPrc = subprocess.Popen(['jq \'.items[] | select ( .spec.rules[].http.paths[].backend.service.name == "'+k8sSvcName+
                                    '")\' '+ ingressFileName+' | jq \'.metadata.namespace\''], shell=True, stdout = subprocess.PIPE) 
                            
                            k8sNameSpace = str(subPrc.communicate()[0].decode("utf-8"))
                            k8sNameSpace.replace("\"","")
                            if(k8sNameSpace.find("\n")):
                                k8sNameSpace=k8sNameSpace.split("\n")
                                k8sNameSpace = trimAndRemoveDoubleQuotes(k8sNameSpace[0])

                            print("K8S-Namespace: "+ k8sNameSpace)

                            
                            

                            #----------------------------------------------
                            # Busca k8s svc selectorApp
                            #----------------------------------------------

                            if(len(k8sSvcName) > 0 and len(k8sNameSpace)>0):
                                subPrc = subprocess.Popen(['kubectl get svc '+k8sSvcName+' -n '+k8sNameSpace+' -o json | jq \'.spec.selector.app\''], shell=True, stdout = subprocess.PIPE)
                                selectorApp = str(subPrc.communicate()[0].decode("utf-8"))
                                selectorApp = trimAndRemoveDoubleQuotes(selectorApp)
                            
                            print("K8S-selectorApp: "+ selectorApp)
                            
                            

                            if(len(selectorApp) > 0):
                                #----------------------------------------------
                                # Busca k8s deployment name
                                #----------------------------------------------
                                subPrc = subprocess.Popen(['kubectl get deploy -n '+k8sNameSpace+' -o json | jq \'.items[] | select(.spec.template.metadata.labels.app == "'+selectorApp+'" )\' | jq \'.metadata.name\' '], shell=True, stdout = subprocess.PIPE) 
                                k8sDeployName = str(subPrc.communicate()[0].decode("utf-8"))
                                k8sDeployName = trimAndRemoveDoubleQuotes(k8sDeployName)
                            print("K8S-deployName: "+ k8sDeployName)

                            print("------")
                    
            myFile.write( ( routeId ) +csvSeparator)
            myFile.write(( path )+csvSeparator)
            myFile.write(( svcName )+csvSeparator)
            myFile.write(( svcId )+csvSeparator)
            myFile.write(( svcUpPath )+csvSeparator)
            myFile.write(( svcPlugins )+csvSeparator)
            myFile.write(( albDNS  )+csvSeparator)
            myFile.write(( k8sSvcName  )+csvSeparator)
            myFile.write(( k8sNameSpace )+csvSeparator)
            myFile.write(( selectorApp  )+csvSeparator)
            myFile.write(( k8sDeployName )+csvSeparator)
            myFile.write(( dicc_text ))
            myFile.write("\n")

            path=""
            routeId=""
            kongSvcName=""
            svcId=""
            svcUpPath=""
            svcPlugins=""
            albDNS=""
            svcName=""
            k8sSvcName=""
            k8sNameSpace=""
            selectorApp=""
            dicc_text=""

    myFile.close()

#end genCSV()

#  Descargar json de servicios kong
serviceFile1 = "kong-services.json"
serviceFile2 = "kong-services-next.json"
ingressFile = "k8s-ingress.json"
routeFile1 = "kong-routes.json"
routeFile2 = "kong-routes-next.json"

host_port_kong = "localhost:8001"

url = "http://"+host_port_kong+"/services"
downloadJson(url,serviceFile1)
subPrc = subprocess.Popen(['jq','.next',serviceFile1] , stdout = subprocess.PIPE) 
nextToken = str(subPrc.communicate()[0].decode("utf-8"))
nextToken=nextToken.lstrip().rstrip()
nextToken=nextToken[1:len(nextToken)-1]
print(nextToken)

if(len(nextToken)>10):
    downloadJson("http://"+host_port_kong+nextToken, serviceFile2)

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

# Descargar json de ingress
# subPrc = subprocess.Popen(['k8s-desa'] , shell=True) 
# subPrc = subprocess.Popen(['kubectl get ingress -A -o json > '+ingressFile] , shell=True) 

routesFileNames = [routeFile1,routeFile2]
servicesFileNames = [serviceFile1,serviceFile2]
# generar Excel
genCSV(ingressFileName=ingressFile, routesFileNames=routesFileNames,servicesFileNames=servicesFileNames)


# https://stackoverflow.com/questions/7353054/running-a-command-line-containing-pipes-and-displaying-result-to-stdout