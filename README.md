# LFIre
A tool which detects Local File Inclusion vulnerability, exploits it and spawns a shell.

## How does it work?
It works by testing for the readibility of file **/etc/passwd** on multiple levels:

```
Test 1: /etc/passwd
Test 2: ../etc/passwd
Test 3: ../../etc/passwd
Test n: ../../../..<long_chain>../../etc/passwd
```

By going multiple levels, it looks for the string "root:x:0:0" to confirm if the LFI was successful. 

## Note
Currently it's in testing phase so much of the functionality is yet to be added.
