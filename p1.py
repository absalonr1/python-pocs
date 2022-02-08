import subprocess
import re

routesFileName="routes-sub.json"
servicesFileName="services.json"

subPrc = subprocess.Popen(['jq','(.data[].paths[])',routesFileName], stdout = subprocess.PIPE) 
pathArray = str(subPrc.communicate()[0].decode("utf-8")) 
pathArray = pathArray.split('\n')

# for each Path
#print(len(pathArray))
bufsize = 1
myFile = open('summary.csv', 'w', buffering=bufsize)

csvSeparator = ","

myFile.write("path"+csvSeparator)
myFile.write("svcId"+csvSeparator)
myFile.write("albDNS"+csvSeparator)
myFile.write("svcName"+csvSeparator)
myFile.write("k8sSvcName"+csvSeparator)
myFile.write("k8sNameSpace"+csvSeparator)
myFile.write("selectorApp"+csvSeparator)
myFile.write("k8sDeployName\n")

path=""
svcId=""
albDNS=""
svcName=""
k8sSvcName=""
k8sNameSpace=""
selectorApp=""
k8sDeployName=""

for path in pathArray:
    if(len(path) > 1):
        print("Route Path: "+ path)
        subPrc = subprocess.Popen(['jq','.data[] | select (.paths[0] == '+path+')',routesFileName], stdout = subprocess.PIPE) 
        subPrc2 = subprocess.Popen(['jq','.service.id'], stdin=subPrc.stdout, stdout = subprocess.PIPE) 
        svcId = str(subPrc2.communicate()[0].decode("utf-8"))
        svcId=svcId.lstrip().rstrip()
        print("Service ID: "+ svcId)

        if(len(svcId)>38):
            svcId="ERROR: Mas de un service para el path"
        else:
            subPrc = subprocess.Popen(['jq','(.data[] | select (.id == '+svcId+' ) )',servicesFileName], stdout = subprocess.PIPE) 
            subPrc2 = subprocess.Popen(['jq','.host'], stdin=subPrc.stdout, stdout = subprocess.PIPE)
            albDNS = str(subPrc2.communicate()[0].decode("utf-8"))
            albDNS = albDNS.lstrip().rstrip()
            print("ALB DNS: "+ albDNS)
            
            
            if(re.match("[0-9]+\.[0-9]+\.[0-9]+\.[0-9]+",albDNS[1:len(albDNS)-1]) is None ):
                subPrc = subprocess.Popen(['jq','(.data[] | select (.id == '+svcId+' ) )',servicesFileName], stdout = subprocess.PIPE) 
                subPrc2 = subprocess.Popen(['jq','.name'], stdin=subPrc.stdout, stdout = subprocess.PIPE) 
                svcName = str(subPrc2.communicate()[0].decode("utf-8"))
                svcName = svcName.lstrip().rstrip()
                print("Service NAME: "+ svcName)

                # quitar comillas dobles al inicio y al final
                path = path[1:len(path)-1]

                path1=""
                path2=""
                path3=""
                path4=""

                if(path.endswith("/")):
                    path1=path
                    path2=path+"*"
                    path3=path[0:len(path)-1]+"*"
                    path4=path[0:len(path)-1]
                else:
                    path1=path
                    path2=path+"*"
                    path3=path+"/*"
                    path4=path+"/"
                print("\t"+path1)
                print("\t"+path2)
                print("\t"+path3)
                print("\t"+path4)
                
                #jq '.items[] | select ( .status.loadBalancer.ingress[].hostname == "internal-k8s-ingresspyme2c-deffada9e5-1182658737.us-west-2.elb.amazonaws.com" and ( .spec.rules[].http.paths[].path == "/api/pyme2c/compensations/v1" or .spec.rules[].http.paths[].path == "/api/pyme2c/compensations/v1/" or .spec.rules[].http.paths[].path == "/api/pyme2c/compensations/v1/*" or .spec.rules[].http.paths[].path == "/api/pyme2c/compensations/v1*")) ' ingress.json | jq '.spec.rules[].http.paths[0].backend.service.name'
                
                subPrc = subprocess.Popen(['jq','.items[] | select ( .status.loadBalancer.ingress[].hostname == '+albDNS+' and ( .spec.rules[].http.paths[].path == "'+path1+'" or .spec.rules[].http.paths[].path == "'+path2+'" or .spec.rules[].http.paths[].path == "'+path3+'" or .spec.rules[].http.paths[].path == "'+path4+'"))','ingress.json'], stdout = subprocess.PIPE) 
                subPrc2 = subprocess.Popen(['jq','.spec.rules[].http.paths[0].backend.service.name'], stdin=subPrc.stdout, stdout = subprocess.PIPE) 
                k8sSvcName = str(subPrc2.communicate()[0].decode("utf-8"))
                k8sSvcName = k8sSvcName.lstrip().rstrip()
                k8sSvcName= k8sSvcName[1:len(k8sSvcName)-1]
                print("K8S-Service NAME: "+ k8sSvcName)

                subPrc = subprocess.Popen(['jq','.items[] | select ( .status.loadBalancer.ingress[].hostname == '+albDNS+' and ( .spec.rules[].http.paths[].path == "'+path1+'" or .spec.rules[].http.paths[].path == "'+path2+'" or .spec.rules[].http.paths[].path == "'+path3+'" or .spec.rules[].http.paths[].path == "'+path4+'"))','ingress.json'], stdout = subprocess.PIPE) 
                subPrc2 = subprocess.Popen(['jq','.metadata.namespace'], stdin=subPrc.stdout, stdout = subprocess.PIPE) 
                k8sNameSpace = str(subPrc2.communicate()[0].decode("utf-8"))
                k8sNameSpace = k8sNameSpace.lstrip().rstrip()
                k8sNameSpace= k8sNameSpace[1:len(k8sNameSpace)-1]
                print("K8S-Namespace: "+ k8sNameSpace)

                # Route Path: "/api/container/core/v1"
                # Service ID: "8377c5a7-d145-40c2-a48f-afb0f90d8038"
                # ALB DNS: "internal-k8s-ingresscontainer-fcc9610877-445198957.us-west-2.elb.amazonaws.com"
                # Service NAME: "dev-srv00019-cross-front-contain"
                # K8S-Service NAME: "ms-container-core"
                # K8S-Namespace: "dev-ns-containers"

                # obtener selector app de k8s para el svc
                # k get svc ms-salida-ruta -n dev-ns-retiro -o json | jq '.spec.selector.app'

                subPrc = subprocess.Popen(['kubectl get svc '+k8sSvcName+' -n '+k8sNameSpace+' -o json'], shell=True, stdout = subprocess.PIPE) 
                subPrc2 = subprocess.Popen(['jq','.spec.selector.app'], stdin=subPrc.stdout, stdout = subprocess.PIPE)  
                selectorApp = str(subPrc2.communicate()[0].decode("utf-8"))
                selectorApp = selectorApp.lstrip().rstrip()
                print("K8S-selectorApp: "+ selectorApp) 
                
                print("command: "+'kubectl get deploy -n '+k8sNameSpace+' -o json |'+ 'jq .items[] | select(.spec.template.metadata.labels.app == '+selectorApp+' ) | jq .metadata.name')
                subPrc = subprocess.Popen(['kubectl get deploy -n '+k8sNameSpace+' -o json'], shell=True, stdout = subprocess.PIPE) 
                subPrc2 = subprocess.Popen(['jq','.items[] | select(.spec.template.metadata.labels.app == '+selectorApp+' )'], stdin=subPrc.stdout, stdout = subprocess.PIPE)  
                subPrc3 = subprocess.Popen(['jq','.metadata.name'], stdin=subPrc2.stdout, stdout = subprocess.PIPE)  
                k8sDeployName = str(subPrc3.communicate()[0].decode("utf-8"))
                k8sDeployName = k8sDeployName.lstrip().rstrip()
                print("K8S-deployName: "+ k8sDeployName)

                print("------")
        
        myFile.write(path+csvSeparator)
        myFile.write(svcId+csvSeparator)
        myFile.write(albDNS+csvSeparator)
        myFile.write(svcName+csvSeparator)
        myFile.write(k8sSvcName+csvSeparator)
        myFile.write(k8sNameSpace+csvSeparator)
        myFile.write(selectorApp+csvSeparator)
        myFile.write(k8sDeployName)
        myFile.write("\n")

        path=""
        svcId=""
        albDNS=""
        svcName=""
        k8sSvcName=""
        k8sNameSpace=""
        selectorApp=""
        k8sDeployName=""

myFile.close()





# def func1(param1=4):
#     """
#     sdsdsdsds
#     sdsds
#     """
#     print("func1:"+str(param1))
#     return "Retorno"

# print("hola")

# var = 77
# print(var)



# print(func1(11))



# https://stackoverflow.com/questions/7353054/running-a-command-line-containing-pipes-and-displaying-result-to-stdout