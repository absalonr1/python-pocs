import csv
import subprocess
from urlmatch import urlmatch

def parchar(serviceId,newDNS):
    patchService = "curl -i -s -X PATCH http://localhost:8001/services/"+serviceId
    patchService += " --data \"host="+newDNS+"\""
    subPrc = subprocess.Popen([patchService],shell=True, stdout=subprocess.PIPE)
    out = str(subPrc.communicate()[0].decode("utf-8"))
    flagPatched=False
    out = out.split("\n")
    for item in out:
        #print(item+"\n")
        if(item.startswith("HTTP/1.1 ")):
            if(item.find("200")):
                flagPatched=True
                #print("patched OK")
                return True
    # if(not flagPatched):
    #     print("patched NO OK!!")
    return False

#http://localhost:8899/#/services/bf7eea1f-6d63-4185-8ec8-0286c9dfc63d
#http://localhost:8899/#/services/99d0f78a-4857-4423-b6f5-01b2122b827e

kongSvcDic = dict()
# kongSvcDic = {
#     "bf7eea1f-6d63-4185-8ec8-0286c9dfc63d":["/a/b","dns-new.test.cl"],
#     "99d0f78a-4857-4423-b6f5-01b2122b827e":["/o/p/q","host.deleteme333"]
# }

# jq '.data[] | .id + "," + .path + "," + .host' services-prod.json > summary-services-prod.csv
with open('summary-services-prod.csv') as csvFile:
    csvReader = csv.reader(csvFile, delimiter=',')
    for row in csvReader:
        kongSvcDic[row[0]]= [row[1],row[2]]

# if(True):
#     quit()

# itero por casa Ingress (path/dns)
with open('test.csv') as csv_file:
    csv_reader = csv.reader(csv_file, delimiter=',')
    line_count = 0
    for row in csv_reader:
        ingressPath=row[0]
        newDNS=row[1]
        # itero por cada service de Kong
        flagServicePatched=False
        for key in kongSvcDic.keys():
            servicePath = kongSvcDic[key][0]
            serviceId = key
            match_pattern = 'http://host' + ingressPath
            match = urlmatch(match_pattern, 'http://host' + servicePath)
            if (not match and not servicePath.endswith("/")):
                temp_servicePath = servicePath + "/"
                match = urlmatch(match_pattern, 'http://host' + temp_servicePath)
                #print(match_pattern + " | " + "http://host" + temp_servicePath + "-->" + str(match))
            if (match):
                flagServicePatched = parchar(serviceId,newDNS)
                break
        if(not flagServicePatched):
            print("["+ingressPath+"] Not patched")
        else:
            print("[ "+serviceId + " --> " + servicePath + " ] patched with: [" + newDNS + ", match: "+ingressPath+"]")
