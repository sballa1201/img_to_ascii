# img_to_ascii
Turn an image/video into its asciified variant.
```sh
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
                        Optional argument for a string specifying which ascii characters are permitted.
                        The empty character space, " ", is not included by unless specified.
                        Escaping certain characters may be required.
                        The default is: " !$^*()-+=|\/><~\#@^8:.,"
  -t TTF, --ttf TTF     Specify the file path for the TrueType Font to be used. The default font used is "dejavu-sans-mono".
  -v, --video           If the input is a video this must be enabled.
```
# Examples
In the examples below, the right image is the original, the middle is converted using the default character set and the left image is converted using the character set "░▒▓█ ". For the gif the "--video" tag was used.

![alt text](Examples/example1.png "Mic Man")

![alt text](Examples/example2.png "Tux")

![alt text](Examples/example3.png "Tesseract")
# How it works
We make the image graycale and then split it into rectangular tiles that are the same size as the font we are using (16 x 8). For each tile, we then compute the "closest" ascii character to it. This is done by first converting the tile and each ascii character, which is a 16x8 matrix, into a 16x8=128 length vector (concatenate the rows). We then find the closest ascii charcacter geometrically (any norm in this 128 dimensional space works, we use L1 for simplicity).

The result of this is that edges are more accurately represented as well as any set of characters can be used, at the cost of more computation.
