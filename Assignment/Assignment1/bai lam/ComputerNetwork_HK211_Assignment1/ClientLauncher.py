import sys
import socket
from tkinter import Tk
from Client1 import Client

if __name__ == "__main__":
    try:
        serverAddr = sys.argv[1]
        serverPort = sys.argv[2]
        rtpPort = sys.argv[3]
        fileNameList = sys.argv[4]

        if serverAddr == "localhost":
            hostname = socket.gethostname()
            local_ip = socket.gethostbyname(hostname)
            serverAddr = local_ip
    except:
        print("[Usage: ClientLauncher.py Server_name Server_port RTP_port Video_file]\n")

    root = Tk()
    """
    # Create a new client
    serverAddr = "localhost"
    if serverAddr == "localhost":
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("8.8.8.8", 80))
        local_ip = s.getsockname()[0]
        serverAddr = local_ip
    serverPort = 1200
    rtpPort = 5008
    fileNameList = "[movie.Mjpeg,movie.Mjpeg]"""

    # Create a new client (by command line)
    app = Client(root, serverAddr, serverPort, rtpPort, fileNameList)
    app.master.title("RTPClient")
    root.mainloop()
