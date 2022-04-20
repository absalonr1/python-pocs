import requests


req = requests.get("https://jsonplaceholder.typicode.com/todos/1")
print("Req"+str(req))