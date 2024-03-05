# img_to_ascii
Turn an image/video into its asciified variant.
```shell
[user@user img_to_ascii]$ python img_to_ascii.py -h
usage: img_to_ascii.py [-h] -i INPUT -o OUTPUT [-c CHARS] [-t TTF] [-v]

Converts image to its asciified variant

options:
  -h, --help            show this help message and exit
  -i INPUT, --input INPUT
                        File path for the input file.
  -o OUTPUT, --output OUTPUT
                        File path for the output.
  -c CHARS, --chars CHARS
                        Optional argument for a string specifying which ascii characters are permitted. The empty character space, \" \", is not included by unless specified. Escaping certain characters may be required. The default is: \"
                        !$^*()-+=`|\/><~#@^8:.,\"
  -t TTF, --ttf TTF     Specify the file path for the TrueType Font to be used. The default font used is "dejavu-sans-mono"
  -v, --video           If the input is a video this must be enabled.
```
