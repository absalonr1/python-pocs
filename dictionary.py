from os import PRIO_USER


sampleDic = {
                "a":
                    {
                        "b":
                            {
                                "c":None
                            },
                        "b1":
                            {
                                "c1":None
                            }
                    }
                ,
                "m":
                    {
                        "n":
                            {
                                "o": None
                            },
                        "n1":
                            {
                                "o1": None
                            }
                    }
            }
#print(sampleDic)

root = dict()

def addNode(key, elemsList):
    print(key)
    print(elemsList)

def updateTree(elemsList):
    #print(elemsList)
    for e in elemsList:
        if(root.get(elemsList[0]) == None):
            addNode(elemsList[0],elemsList[1:len(elemsList)])
            break
        else:
            updateTree()


paths = ["/a/b/c", "/a/b1/c1", "/m/n/o","/m/n1/o1"]

for path in paths:
    pathElements = path.split("/")
    pathElements = pathElements[1:len(pathElements)]
    updateTree(pathElements)
    # for element in pathElements:
    #     if(len(element)==0):
    #         continue

