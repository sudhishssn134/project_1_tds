import os
from fastapi import FastAPI, HTTPException
from fastapi.responses import PlainTextResponse
from fastapi.middleware.cors import CORSMiddleware
import uvicorn
import json
import base64
import requests
import subprocess

api = FastAPI()

api.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allows all origins
    allow_credentials=True,
    allow_methods=["*"],  # Allows all methods (GET, POST, OPTIONS, etc.)
    allow_headers=["*"],  # Allows all headers
)
AIPROXY_TOKEN = os.getenv("AIPROXY_TOKEN")
response_format = {
    "type":"json_schema",
    "json_schema":{
        "name":"task_runner",
        "schema":{
            "type":"object",
            "required":["python_dependencies", "python_code"],
            "properties":{
                "python_code":{
                    "type":"string",
                    "description":"Python code to perform tasks"
                },
                "python_dependencies":{
                    'type':"array",
                    "items":{
                        "type":"object",
                        "properties":{
                            "module":{
                                "type":"string",
                                "description":"Name of the python module"

                            }
                        },
                    "required":["module"],
                        "additionalProperties":False
                    }
                }
            }
        }
    }
}
primary_prompt = """The text beside primary_prompt is:
You are an automated agent, so generate python code that does the specified task.
Assume uv and python is preinstalled.
Assume that code you generate will be executed inside a docker container.
Inorder to perform any task if some python package is required to install, provide name of those modules.
If the Task contains file path in it, then remove any "/" present at the starting of the path
If the task includes reading files, then carefully see the task and include all the possible formats of the data given in the task.
Do not handle any errors
"""

def get_files():
    # Define the script URL and user email
    script_url = 'https://raw.githubusercontent.com/sanand0/tools-in-data-science-public/tds-2025-01/project-1/datagen.py?$24f2002533@ds.study.iitm.ac.in'
    response = requests.get(script_url)
    rt = response.text
    f = open("datagen.py", "w")
    f.write(rt)
    f.close()
    subprocess.run(["uvicorn", "run", "datagen.py", "24f2002533@ds.study.iitm.ac.in"])
def llm_executor(task, error=None):
    with open("code_execute.py", "r") as f:
        code = f.read()
    f.close()
    primary_prompt = f"""The following code was generated for the given task. This error has occured. 
    Fix This Error, without ignoring any values in the file. Get some suitable method to solve the error.
    -----------------
    The Task
    {task}
    -----------------
    The Code 
    ```python
    {code}
    ```
    -----------------
    The Error Encountered
    {error}
    -----------------
    """
    url = 'https://aiproxy.sanand.workers.dev/openai/v1/chat/completions'  # Replace with the actual URL of the LLM image processing service
    head = {
        "Authorization": f"Bearer {AIPROXY_TOKEN}",
        "Content-Type": "application/json"}
    data = {"model": "gpt-4o-mini", "messages": [
        {
            "role": "system",
            "content": f"""{primary_prompt}"""
        },
        {"role": "user",
         "content": task}],
            "response_format": response_format}
    response = requests.post(url, headers=head, json=data)
    if response.status_code == 200:
        task = (response.json()['choices'][0]['message']['content'])
        python_dependencies = json.loads(task)['python_dependencies']
        python_code = json.loads(task)['python_code']
        f = open("code_execute.py", "w")
        f.write(python_code)
        f.close()
        output = subprocess.run(["python", "code_execute.py"], capture_output=True, text=True, cwd=os.getcwd())
        st_error = output.stderr.split("\n")
        st_output = output.stdout
        st_r = output.returncode
        try:
            for i in range(len(st_error)):
                if st_error[i].strip().startswith("File"):
                    raise Exception(st_error[i:])
            return {"success": 1}
        except Exception as e:
            return {'error': e}
    elif response.status_code == 500:
        return {'error': "Error-S2"}
    else:
        return {'error': "Error-S1"}
def task_runner(task):
    url = 'https://aiproxy.sanand.workers.dev/openai/v1/chat/completions'  # Replace with the actual URL of the LLM image processing service
    head = {
        "Authorization": f"Bearer {AIPROXY_TOKEN}",
        "Content-Type": "application/json"}
    data = {"model": "gpt-4o-mini", "messages": [
        {
            "role":"system",
            "content":f"""{primary_prompt}"""
        },
        {"role": "user",
         "content": task}],
            "response_format":response_format}
    response = requests.post(url, headers=head, json=data)
    if response.status_code == 200:
        task = (response.json()['choices'][0]['message']['content'])
        python_dependencies = json.loads(task)['python_dependencies']
        python_code = json.loads(task)['python_code']
        f = open("code_execute.py", "w")
        f.write(python_code)
        f.close()
        output = subprocess.run(["python", "code_execute.py"], capture_output=True, text=True, cwd=os.getcwd())
        st_error = output.stderr.split("\n")
        st_output = output.stdout
        st_r = output.returncode
        try:
            for i in range(len(st_error)):
                if st_error[i].strip().startswith("File"):
                    raise Exception(st_error[i:])
            return {"success":1}
        except Exception as e:
            return {'error':e}
    elif response.status_code == 500:
        return {'error':"Error-S2"}
    else:
        return {'error':"Error-S1"}


@api.post("/run")
def project_1(task: str):
    output = task_runner(task)
    if "https://raw.githubusercontent.com/sanand0/tools-in-data-science-public/tds-2025-01" in task:
        get_files()
        raise HTTPException(status_code=200, detail="OK")
    if "success" in output:
        return "Success"
    elif "error" in output:
        if output["error"] == "Error-S2":
            raise HTTPException(status_code=500, detail="Internal Server Error")
        elif output["error"] == "Error-S1":
            raise HTTPException(status_code=400, detail="Bad Request")
        else:
            count = 0
            while count < 2:
                out = llm_executor(task, output['error'])
                if "success" in out:
                    raise HTTPException(status_code=200, detail="OK")
                count += 1
            raise HTTPException(status_code=400, detail="Bad Request")


@api.get("/read")
def project_1_check(path):
    try:
        f = open(path, "r")
        contents = f.read()
        return PlainTextResponse(content=contents, status_code=200)
    except FileNotFoundError:
        raise HTTPException(status_code=404, detail="Not Found")


if __name__ == "__main__":
  (uvicorn.run(api, host="0.0.0.0", port=8000))


