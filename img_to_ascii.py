from PIL import Image, ImageDraw, ImageFont
import numpy as np_1
import numpy as np
import argparse
import time

f_size = 12
block_w = 8
block_h = 16

#f_size = 6
#block_w = 4
#block_h = 8


def letterToArray(c, ttfPath):
    #draw the letter then convert it into an array

    image = Image.new("L", (block_w, block_h), "black") 
    draw = ImageDraw.Draw(image) 
    font = ImageFont.truetype(ttfPath, f_size) 
    draw.text((1, 0), c, font=font, fill="white") 

    return np.array(image)

# distance between 2 arrays of same dimensions (here we use sum of absolute difference elementwise)
def dist(x,y):
    # converting the matrix elements to int to avoid unsigned int overflow errors
    return np.sum(np.concatenate(np.absolute(np.subtract(x.astype(int),y.astype(int)))))

# return grayscale npArray as npArray to be processed given the image filepath
def getImgAsArray(filePath):
    png = Image.open(filePath).convert('RGBA')
    background = Image.new('RGBA', png.size, (255, 255, 255))
    imgArr = Image.alpha_composite(background, png)
    imgArr = imgArr.convert('RGB').convert('L')
    return np.array(imgArr)

# returns dictionary of {key: ascii_char, value: bitmap}, given the list of allowedChars (list of chars or string is permissable)
def getAsciiMap(allowedChars, ttfPath):
    matMap = {}
    for c in allowedChars:
        if c not in matMap:
            matMap[c] = letterToArray(c, ttfPath)
    
    return matMap


# get the closest ascii image to the image array given a dictionary of ascii_char:bitmap, without GPU
def getClosestAsciiArrNoGPU(imgArr ,matMap):
    height, width = imgArr.shape

    wSplit = width // block_w
    hSplit = height // block_h
    # truncate image to fit the ascii block size
    imgArr = imgArr[0:(hSplit*block_h) , 0:(wSplit*block_w)]
    imgArr = np.hsplit(imgArr, wSplit)

    # loop over every block and find the nearest ascii char for that block
    for i in range(wSplit):
        col = np.vsplit(imgArr[i], hSplit)
        for j in range(hSplit):
            currChar = ""
            minVal = -1

            for c in matMap:
                d = dist(matMap[c], col[j])
                if d < minVal or minVal < 0:
                    currChar = c
                    minVal = d

            col[j] = matMap[currChar]

        imgArr[i] = np.concatenate(col, 0)

    return np.concatenate(imgArr, 1)




# disabled since overhead costs are too high
# get the closest ascii image to the image array given a dictionary of ascii_char:bitmap, with GPU, uses SIMD
def getClosestAsciiArrGPU(imgArr_gpu ,matMap):
    device = np.cuda.Device()
    memory_pool = np.cuda.MemoryPool()
    np.cuda.set_allocator(memory_pool.malloc)

    height, width = imgArr_gpu.shape

    wSplit = width // block_w
    hSplit = height // block_h
    # truncate image to fit the ascii block size

    tot = 10

    #@np.fuse()
    def gpu_kernel(inp):
        currChar = ""
        minVal = -1

        for c in matMap:
            d = np.sum(np.concatenate(np.absolute(np.subtract(matMap[c].astype(int),inp.astype(int)))))
            if d < minVal or minVal < 0:
                currChar = c
                minVal = d
        return matMap[currChar]

    concat_stream = np.cuda.stream.Stream()
    map_streams = [np.cuda.stream.Stream(non_blocking=True) for _ in range(tot)]
    #map_streams = [[np.cuda.stream.Stream() for _ in range(hSplit)] for _ in range(wSplit)]
    stop_events = []

    #imgArr_gpu = np.asarray(imgArr)


    imgArr_gpu = imgArr_gpu[0:(hSplit*block_h) , 0:(wSplit*block_w)]
    imgArr_gpu = np.hsplit(imgArr_gpu, wSplit)

    for i in range(wSplit):
        imgArr_gpu[i] = np.vsplit(imgArr_gpu[i], hSplit)


    count = 0
    for i in range(wSplit):
        for j in range(hSplit):
            with map_streams[count % tot]:
                imgArr_gpu[i][j] = gpu_kernel(imgArr_gpu[i][j])
                stop_event = map_streams[count % tot].record()
                stop_events.append(stop_event)
            
            count += 1

    for i in range(wSplit*hSplit):
        concat_stream.wait_event(stop_events[i])
    
    #print(imgArr_gpu[0].shape)
    with concat_stream:
        for i in range(wSplit):
            imgArr_gpu[i] = np.concatenate(imgArr_gpu[i], 0)
        imgArr_gpu = np.concatenate(imgArr_gpu, 1)

    device.synchronize()

    for s in map_streams:
        memory_pool.free_all_blocks(stream=s)

    return np.asnumpy(imgArr_gpu)


# save the image array to the specified location
def saveImg(outArr, filePath):
    Image.fromarray(outArr).save(filePath)

#[' .:!+*e$@8']
#allowedChars = " !\$^*()-+=|\\/><~#@^8:.,"
#'░▒▓█ '

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Converts image to its asciified variant')
    parser.add_argument('-i','--input', help='File path for the input file.', required=True)
    parser.add_argument('-o','--output', help='File path for the output.', required=True)
    parser.add_argument('-c','--chars', help='Optional argument for a string specifying which ascii characters are permitted.\nThe empty character space, " ", is not included by unless specified.\nEscaping certain characters may be required.\nThe default is: " !$^*()-+=`|\\/><~#@^8:.,"', required=False, default=" !$^*()-+=|\\/><~#@^8:.,")
    parser.add_argument('-t','--ttf', help='Specify the file path for the TrueType Font to be used. The default font used is "dejavu-sans-mono".', required=False, default="dejavu-sans-mono/DejaVuSansMono.ttf")
    parser.add_argument('-v','--video', help='If the input is a video this must be enabled.', action='store_true')
    #parser.add_argument('-g','--gpu', help='EXPERIMENTAL. Enables the use of your GPU. GPU must be compatible with CuPy. See the CuPy installation page "https://docs.cupy.dev/en/stable/install.html" for details.', action='store_true')
    args = vars(parser.parse_args())

    getClosestAsciiArr = getClosestAsciiArrNoGPU

    allowedChars = args['chars']
    inputFilename = args['input']
    outputFilename = args['output']

#    if args['gpu']:
#        import cupy as np
#        import numpy as np_1
#        getClosestAsciiArr = getClosestAsciiArrGPU
    
    matMap = getAsciiMap(allowedChars, args['ttf'])
        

    if args['video']:
        import ffmpeg

        probe = ffmpeg.probe(inputFilename)
        video_stream = next((stream for stream in probe['streams'] if stream['codec_type'] == 'video'), None)
        width = int(video_stream['width'])
        height = int(video_stream['height'])
        probe = ffmpeg.probe(inputFilename)
        video_info = next(s for s in probe['streams'] if s['codec_type'] == 'video')
        frames = int(video_stream['nb_frames'])

        process1 = (
            ffmpeg
            .input(inputFilename)
            .output('pipe:', format='rawvideo', pix_fmt='gray', vframes=frames)
            .run_async(pipe_stdout=True)
        )

        process2 = (
            ffmpeg
            .input('pipe:', format='rawvideo', pix_fmt='gray', s='{}x{}'.format(width, height))
            .output(outputFilename, pix_fmt='gray')
            .overwrite_output()
            .run_async(pipe_stdin=True)
        )

        i = 0
        while i < frames:
            inBytes = process1.stdout.read(width * height)
            if not inBytes:
                break

            inFrame = (
                np
                .frombuffer(inBytes, np.uint8)
                .reshape([height, width])
            )

            # convert frame to grayscale
            imgArr = getClosestAsciiArr(inFrame, matMap)

            process2.stdin.write(
                imgArr
                .astype(np.uint8)
                .tobytes()
            )
            i += 1
        

        
        

    else:
        
        imgArr = getImgAsArray(inputFilename)
        start_time = time.time()
        outArr = getClosestAsciiArr(imgArr ,matMap)
        elapsed_time = time.time() - start_time
#        if args['gpu']:
#            outArr = np.asnumpy(outArr)
        saveImg(outArr, outputFilename)