import subprocess

def ping(servers):
    
    # The command you want to execute   
    cmd = 'ping'
  
    # send one packet of data to the host 
    # this is specified by '-c 1' in the argument list 
    outputlist = []
    # Iterate over all the servers in the list and ping each server
    for server in servers:
        temp = subprocess.Popen([cmd, '-c 1', server], stdout = subprocess.PIPE) 
        # get the output as a string
        output = str(temp.communicate()) 
    # store the output in the list
        outputlist.append(output)
    return outputlist

# servers = list(open('servers.txt'))


# for i in range(len(servers)):
#     servers[i] = servers[i].strip('\n')
#     outputlist = ping(servers) 
# print(outputlist)


subPrc = subprocess.Popen(['jq','(.data[].paths[])','routes-sub.json'], stdout = subprocess.PIPE) 
pathArray = str(subPrc.communicate()[0].decode("utf-8")) 
pathArray = pathArray.split('\n')

# for each Path
#print(len(pathArray))
for path in pathArray:
    if(len(path) > 1):
        print("Route Path: "+ path)
        subPrc = subprocess.Popen(['jq','.data[] | select (.paths[0] == '+path+')','routes-sub.json'], stdout = subprocess.PIPE) 
        subPrc2 = subprocess.Popen(['jq','.service.id'], stdin=subPrc.stdout, stdout = subprocess.PIPE) 
        svcId = str(subPrc2.communicate()[0].decode("utf-8"))
        svcId=svcId.lstrip().rstrip()
        print("Service ID: "+ svcId)

        subPrc = subprocess.Popen(['jq','(.data[] | select (.id == '+svcId+' ) )','services-sub.json'], stdout = subprocess.PIPE) 
        subPrc2 = subprocess.Popen(['jq','.host'], stdin=subPrc.stdout, stdout = subprocess.PIPE)
        albDNS = str(subPrc2.communicate()[0].decode("utf-8"))
        albDNS = albDNS.lstrip().rstrip()
        print("ALB DNS: "+ albDNS)

        subPrc = subprocess.Popen(['jq','(.data[] | select (.id == '+svcId+' ) )','services-sub.json'], stdout = subprocess.PIPE) 
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
        print("K8S-Service NAME: "+ k8sSvcName)

        print("------")





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