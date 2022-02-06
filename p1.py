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

        subPrc = subprocess.Popen(['jq','(.data[] | select (.id == '+svcId+' ) )','services-sub.json'], stdout = subprocess.PIPE) 
        subPrc2 = subprocess.Popen(['jq','.name'], stdin=subPrc.stdout, stdout = subprocess.PIPE) 
        svcName = str(subPrc2.communicate()[0].decode("utf-8"))
        svcName = svcName.lstrip().rstrip()
        print("Service NAME: "+ svcName)

        #jq '.items[] | select ( .status.loadBalancer.ingress[].hostname == "internal-k8s-ingresspyme2c-deffada9e5-1182658737.us-west-2.elb.amazonaws.com" ) ' ingress.json  | jq '. | select (.spec.rules[].http.paths[].path == "/api/pyme2c/compensations/v1/*" )'| jq '.spec.rules[].http.paths[0].backend.service.name'
        subPrc = subprocess.Popen(['jq','.items[] | select ( .status.loadBalancer.ingress[].hostname == '+albDNS+' )','ingress.json'], stdout = subprocess.PIPE) 
        subPrc2 = subprocess.Popen(['jq','. | select (.spec.rules[].http.paths[].path == "/api/pyme2c/compensations/v1/*" )'], stdin=subPrc.stdout, stdout = subprocess.PIPE) 
        subPrc3 = subprocess.Popen(['jq','.spec.rules[].http.paths[0].backend.service.name'], stdin=subPrc2.stdout, stdout = subprocess.PIPE) 
        k8sSvcName = str(subPrc3.communicate()[0].decode("utf-8"))
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