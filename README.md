# LFIre
A tool which detects Local File Inclusion vulnerability, exploits it and spawns a shell.

## Why I built this?
Back when I was getting started with web application security and learned about Local File Inclusion attack, I decide to automate the whole process to avoid manually checking for file inclusion at each level. So I created this tool.

## How does it work?
It works by testing for the readibility of file **/etc/passwd** on multiple levels:

```
Test 1: /etc/passwd
Test 2: ../etc/passwd
Test 3: ../../etc/passwd
Test n: ../../../..<long_chain>../../etc/passwd
```

By going multiple levels, it looks for the string ```root:x:``` to confirm if the LFI was successful. 
Once the LFI is found, it tries to read shell injectible files like ```/proc/self/environ``` for gainig Remote Code Exeuction through PHP system calls.

## Future Work
* More files to check LFI vulnerability are yet to be added.
* More injectible files are yet to be added.
* PHP wrappers like php:// and zip:// are yet to be added.

## Note
* Currently it's in testing phase so much of the functionality is yet to be added.
* I am aware that /etc/passwd shouldn't be the only file to be tested as it is disallowed in many systems.
* I am aware that other files like /var/log/auth.log can also be used for gaining RCE.
