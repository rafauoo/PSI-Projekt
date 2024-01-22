import subprocess
import time
import threading
import pycurl
import subprocess
import time
import os


def run_docker_compose(): # run docker-compose up --build
    command_docker_compose = ['docker-compose', 'up', '--build']
    subprocess.run(command_docker_compose)

def get_container_ip(container_name): # get container IP
    inspect_command = ['docker', 'inspect', '-f', "'{{range .NetworkSettings.Networks}}{{.IPAddress}}{{end}}'", container_name]
    IP = subprocess.check_output(inspect_command, universal_newlines=True)
    IP = IP.replace("'", "")
    IP = IP.replace("\n", "")
    return IP

def test_curl():
    result = None
    compose_thread = threading.Thread(target=run_docker_compose)
    compose_thread.start() #start docker-compose on another thread

    time.sleep(5) # wait 5 seconds for docker-compose to start
    container_name = 'z23_project_tunnel_client'
    IP = get_container_ip(container_name)
    port = 2137
    c = pycurl.Curl() # create curl object

    try:
        c.setopt(c.URL, f"http://{IP}:{port}") # set url to curl
        c.perform() # perform curl
        http_code = c.getinfo(pycurl.HTTP_CODE) # get http code
        if http_code == 200: 
            result = True
        else:
            result = False

        c.close()
    except Exception as e:
        result = False
    finally:
        subprocess.run(['docker-compose', 'down'])

    assert result is True

def test_wget(): 
    result = None
    compose_thread = threading.Thread(target=run_docker_compose)
    compose_thread.start() #start docker-compose on another thread

    time.sleep(5) # wait 5 seconds for docker-compose to start
    container_name = 'z23_project_tunnel_client'
    IP = get_container_ip(container_name)
    port = 2137

    try:
        subprocess.run(['wget', f"http://{IP}:{port}"]) # perform wget
        output = subprocess.check_output(['cat', 'index.html']).decode().split('\n')[0] # get output from wget
        
        if output == 'Port test successful!': 
            result = True
        else:
            result = False
    except Exception as e:
        result = False
    finally:
        subprocess.run(['docker-compose', 'down'])
        subprocess.run(['rm', 'index.html']) # remove index.html file

    assert result is True

def test_ping():
    result = None
    compose_thread = threading.Thread(target=run_docker_compose)
    compose_thread.start() #start docker-compose on another thread

    time.sleep(5)
    container_name = 'z23_project_tunnel_client'
    IP = get_container_ip(container_name)

    try:
        response = os.popen(f"ping -c 5 {IP}").read() # perform ping
        if '5 received' in response: # check if 5 packets were received
            result = True
        else:
            result = False
        
    except Exception as e:
        result = False
    finally:
        subprocess.run(['docker-compose', 'down'])

    assert result is True
