from urlmatch import urlmatch

from asyncore import write
import subprocess
import re

# python3 -m pip install requests
import requests
#import json



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

def trimAndRemoveDoubleQuotes(string):
    string=string.lstrip().rstrip()
    string=string[1:len(string)-1]
    return string

def genCSV(routesFileName,routesFileName2,servicesFileName,servicesFileName2, ingressFileName):

    bufsize = 1
    myFile = open('summary.csv', 'w', buffering=bufsize)

    csvSeparator = ","

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
    myFile.write("k8sDeployName\n")

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

    subPrc = subprocess.Popen(['jq','(.data[].id)',routesFileName], stdout = subprocess.PIPE) 
    routeIdArray = str(subPrc.communicate()[0].decode("utf-8"))
    routeIdArray = routeIdArray.split('\n')
    
    for routeId in routeIdArray:
        routeId=trimAndRemoveDoubleQuotes(routeId)

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
        subPrc = subprocess.Popen(['jq \'.data[] | select (.id == "'+svcId+'" )\' '+servicesFileName+' | jq \'.name\' '],shell=True, stdout = subprocess.PIPE) 
        svcName = str(subPrc.communicate()[0].decode("utf-8"))
        svcName = trimAndRemoveDoubleQuotes(svcName)
        print("Service NAME: "+ svcName)
        
        
        #---------------------------------
        # Busca kong service upstream path
        #---------------------------------
        subPrc = subprocess.Popen(['jq \'.data[] | select (.id == "'+svcId+'" ) \' '+servicesFileName+' | jq \'.path\' '], shell=True, stdout = subprocess.PIPE) 
        svcUpPath = str(subPrc.communicate()[0].decode("utf-8"))
        svcUpPath =trimAndRemoveDoubleQuotes(svcUpPath)
        print("Service Upstream PATH: "+ svcUpPath)
        
        
        # Identificar los plugins asociados al service
        req = requests.get('http://adminkong.dev.blue.private/services/'+svcId+'/plugins')
        jsonRespDictionary = req.json()
        flagLambda = False
        #print(jsonRespDictionary)
        if(len(jsonRespDictionary)>0):
            for item in jsonRespDictionary["data"]:
                svcPlugins= svcPlugins+"/"+item["name"]
                if(svcPlugins.find("lambda") != -1):
                    flagLambda = True
        print("Kong service plugins: "+svcPlugins)

        
        if(not flagLambda):
            subPrc = subprocess.Popen(['jq \'.data[] | select (.id == "'+svcId+'" )\' '+servicesFileName+' | jq \'.host\' '], shell=True, stdout = subprocess.PIPE) 
            albDNS = str(subPrc.communicate()[0].decode("utf-8"))
            albDNS = trimAndRemoveDoubleQuotes(albDNS)
            print("ALB DNS: "+ albDNS)
            
            

            # no es una IP?
            if(re.match("[0-9]+\.[0-9]+\.[0-9]+\.[0-9]+",albDNS) is None):

                path1=""
                path2=""
                path3=""
                path4=""

                if(svcUpPath.endswith("/")):
                    path1=svcUpPath
                    path2=svcUpPath+"*"
                    path3=svcUpPath+"*"
                    path4=svcUpPath
                else:
                    path1=svcUpPath
                    path2=svcUpPath+"*"
                    path3=svcUpPath+"/*"
                    path4=svcUpPath+"/"
                print("\t"+path1)
                print("\t"+path2)
                print("\t"+path3)
                print("\t"+path4)
                
                #---------------------------------
                # Busca k8s svc name
                #---------------------------------
                
                command = 'jq \'.items[] | select ( .status.loadBalancer.ingress[].hostname == "'+albDNS+'" )\' '+ingressFileName+' | jq \'.spec.rules[].http.paths[0].backend.service.name\''
                print(command)
                subPrc = subprocess.Popen([command], shell=True, stdout = subprocess.PIPE)
                k8sSvcName = str(subPrc.communicate()[0].decode("utf-8"))
                k8sSvcName = trimAndRemoveDoubleQuotes(k8sSvcName)
                print("K8S-Service NAME(s): "+ k8sSvcName)
                
                match_pattern = 'http://host/api/container/*'
                print(urlmatch(match_pattern, 'http://host/api/container/core/v1/'))

                if(True):
                    quit()
                
                #----------------------------------------------
                # Busca k8s svc nameSpace asociado al ingress
                #----------------------------------------------
                subPrc = subprocess.Popen(['jq \'.items[] | select ( .status.loadBalancer.ingress[].hostname == "'+albDNS+
                        '")\' '+ ingressFileName+' | jq \'.metadata.namespace\''], shell=True, stdout = subprocess.PIPE) 
                
                k8sNameSpace = str(subPrc.communicate()[0].decode("utf-8"))
                k8sNameSpace = trimAndRemoveDoubleQuotes(k8sNameSpace)
                print("K8S-Namespace: "+ k8sNameSpace)
                

                #----------------------------------------------
                # Busca k8s svc selectorApp
                #----------------------------------------------

                selectorApp=""
                if(len(k8sSvcName) > 0 and len(k8sNameSpace)>0):
                    subPrc = subprocess.Popen(['kubectl get svc "'+k8sSvcName+'" -n "'+k8sNameSpace+'" -o json \ jq \'.spec.selector.app\''], shell=True, stdout = subprocess.PIPE)
                    selectorApp = str(subPrc.communicate()[0].decode("utf-8"))
                    selectorApp = trimAndRemoveDoubleQuotes(selectorApp)
                
                print("K8S-selectorApp: "+ selectorApp)
                
                

                k8sDeployName=""
                if(len(selectorApp) > 0):
                    #----------------------------------------------
                    # Busca k8s deployment name
                    #----------------------------------------------
                    subPrc = subprocess.Popen(['kubectl get deploy -n "'+k8sNameSpace+'" -o json | jq \'.items[] | select(.spec.template.metadata.labels.app == '+selectorApp+' )\' | jq \'.metadata.name\' '], shell=True, stdout = subprocess.PIPE) 
                    k8sDeployName = str(subPrc.communicate()[0].decode("utf-8"))
                    k8sDeployName = trimAndRemoveDoubleQuotes(k8sDeployName)
                print("K8S-deployName: "+ k8sDeployName)

                print("------")
                
        # fin de una iteracion
        myFile.write(routeId+csvSeparator)
        myFile.write(path+csvSeparator)
        myFile.write(svcName+csvSeparator)
        myFile.write(svcId+csvSeparator)
        myFile.write(svcUpPath+csvSeparator)
        myFile.write(svcPlugins+csvSeparator)
        myFile.write(albDNS+csvSeparator)
        myFile.write(k8sSvcName+csvSeparator)
        myFile.write(k8sNameSpace+csvSeparator)
        myFile.write(selectorApp+csvSeparator)
        myFile.write(k8sDeployName)
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
        k8sDeployName=""

    myFile.close()
    #end genCSV()

#  Descargar json de servicios kong
serviceFile1 = "kong-services.json"
serviceFile2 = "kong-services-next.json"
ingressFile = "k8s-ingress.json"
routeFile1 = "kong-routes.json"
routeFile2 = "kong-routes-next.json"

# url = "http://adminkong.dev.blue.private/services"
# downloadJson(url,serviceFile1)
# subPrc = subprocess.Popen(['jq','.next',serviceFile1] , stdout = subprocess.PIPE) 
# nextToken = str(subPrc.communicate()[0].decode("utf-8"))
# nextToken=nextToken.lstrip().rstrip()
# nextToken=nextToken[1:len(nextToken)-1]
# print(nextToken)

# if(nextToken!="null"):
#     downloadJson("http://adminkong.dev.blue.private"+nextToken, serviceFile2)

# #  Descargar json de routes kong



# url = "http://adminkong.dev.blue.private/routes"
# downloadJson(url,routeFile1)
# subPrc = subprocess.Popen(['jq','.next',routeFile1] , stdout = subprocess.PIPE) 
# nextToken = str(subPrc.communicate()[0].decode("utf-8"))
# nextToken=nextToken.lstrip().rstrip()
# nextToken=nextToken[1:len(nextToken)-1]
# print(nextToken)

# if(nextToken!="null"):
#     downloadJson("http://adminkong.dev.blue.private"+nextToken, routeFile2)

#  Descargar json de ingress
subPrc = subprocess.Popen(['kubectl get ingress -A -o json > '+ingressFile] , shell=True) 

# generar Excel
genCSV(ingressFileName=ingressFile, routesFileName=routeFile1,routesFileName2=routeFile2,servicesFileName=serviceFile1,servicesFileName2=serviceFile2)



# https://stackoverflow.com/questions/7353054/running-a-command-line-containing-pipes-and-displaying-result-to-stdout