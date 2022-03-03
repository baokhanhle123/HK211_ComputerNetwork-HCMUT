from time import time
from tkinter import *
import tkinter.messagebox
from tkinter import messagebox

from PIL import Image, ImageTk
import socket, threading, sys, traceback, os

from RtpPacket import RtpPacket

CACHE_FILE_NAME = "cache-"
CACHE_FILE_EXT = ".jpg"
CACHE_FILE_TEXT = '.txt'


class Client:
    INIT = 0
    READY = 1
    PLAYING = 2
    state = INIT

    SETUP = 0
    PLAY = 1
    PAUSE = 2
    TEARDOWN = 3
    STOP = 4
    DESCRIBE = 5
    SWITCH = 6

    # Initiation..
    def __init__(self, master, serveraddr, serverport, rtpport, fileNameList):
        self.video_list = fileNameList[1:len(fileNameList) - 1]
        self.video_list = self.video_list.split(',')
        print(self.video_list)
        self.video_list_index = 0

        self.master = master
        self.master.protocol("WM_DELETE_WINDOW", self.handler)
        self.timeBox = "0 : 0"
        self.createWidgets()
        self.serverAddr = serveraddr
        self.serverPort = int(serverport)
        self.rtpPort = int(rtpport)
        self.fileName = self.video_list[0]
        self.rtspSeq = 0
        self.sessionId = 0
        self.requestSent = -1
        self.teardownAcked = 0
        self.stoped = 0
        self.connectToServer()
        self.frameNbr = 0

    def createWidgets(self):
        """Build GUI."""
        # Create Setup button
        # self.setup = Button(self.master, width=20, padx=3, pady=3)
        # self.setup["text"] = "Setup"
        # self.setup["command"] = self.setupMovie
        # self.setup.grid(row=1, column=0, padx=2, pady=2)

        # Create Play button
        self.start = Button(self.master, width=20, padx=3, pady=3)
        self.start["text"] = "Play"
        self.start["command"] = self.playMovie
        self.start.grid(row=1, column=0, padx=2, pady=2)

        # Create Pause button
        self.pause = Button(self.master, width=20, padx=3, pady=3)
        self.pause["text"] = "Pause"
        self.pause["command"] = self.pauseMovie
        self.pause.grid(row=1, column=1, padx=2, pady=2)

        # Create Teardown button
        self.teardown = Button(self.master, width=20, padx=3, pady=3)
        self.teardown["text"] = "Teardown"
        self.teardown["command"] = self.exitClient
        self.teardown.grid(row=1, column=2, padx=2, pady=2)

        # Create a label to display the movie
        self.label = Label(self.master, height=19)
        self.label.grid(row=0, column=0, columnspan=4, sticky=W + E + N + S, padx=5, pady=5)

        # Create Stop button
        self.stop = Button(self.master, width=20, padx=3, pady=3)
        self.stop["text"] = "Stop"
        self.stop["command"] = self.setStop
        self.stop.grid(row=1, column=3, padx=2, pady=2)

        # Create Describe button
        self.describe = Button(self.master, width=20, padx=3, pady=3)
        self.describe["text"] = "Describe"
        self.describe["command"] = self.setDescribe
        self.describe.grid(row=1, column=4, padx=2, pady=2)

        # Create Switch button
        self.switch = Button(self.master, width=20, padx=3, pady=3)
        self.switch["text"] = "Switch"
        self.switch["command"] = self.setSwitch
        self.switch.grid(row=1, column=5, padx=2, pady=2)

        # Create time:
        self.status = Label(self.master, text="Watched time : " + str(self.timeBox), bd=1, relief=SUNKEN, anchor=W)
        self.status.grid(row=2, column=0, columnspan=1, sticky=W + E)

    def setupMovie(self):
        """Setup button handler."""
        if self.state == self.INIT:
            self.sendRtspRequest(self.SETUP)

    def exitClient(self):
        """Teardown button handler."""
        self.sendRtspRequest(self.TEARDOWN)
        self.master.destroy()  # Close the gui window
        try:
            os.remove(CACHE_FILE_NAME + str(self.sessionId) + CACHE_FILE_EXT)
        except:
            pass

    def pauseMovie(self):
        """Pause button handler."""
        if self.state == self.PLAYING:
            self.sendRtspRequest(self.PAUSE)

    def playMovie(self):
        """Play button handler."""
        if self.state == self.INIT:
            # os.remove(CACHE_FILE_NAME + str(self.sessionId) + CACHE_FILE_EXT)
            self.sessionId = 0
            self.stoped = 0
            self.setupMovie()
        while self.state == self.INIT:
            continue

        if self.state == self.READY:
            # Create a new thread to listen for RTP packets
            threading.Thread(target=self.listenRtp).start()
            self.playEvent = threading.Event()
            self.playEvent.clear()
            self.sendRtspRequest(self.PLAY)

    def setStop(self):
        self.label.image = None
        self.sendRtspRequest(self.STOP)
        try:
            os.remove(CACHE_FILE_NAME + str(self.sessionId) + CACHE_FILE_EXT)
        except:
            pass

    def setDescribe(self):
        self.sendRtspRequest(self.DESCRIBE)

    def setSwitch(self):
        self.label.image = None
        self.sendRtspRequest(self.SWITCH)
        try:
            os.remove(CACHE_FILE_NAME + str(self.sessionId) + CACHE_FILE_EXT)
        except:
            pass

    def listenRtp(self):
        """Listen for RTP packets."""
        while True:
            try:
                data = self.rtpSocket.recv(20480)
                if data:
                    rtpPacket = RtpPacket()
                    rtpPacket.decode(data)
                    size_payload = str(sys.getsizeof(rtpPacket.getPayload()))
                    time_tr = time() - rtpPacket.timestamp()

                    print('size frame: ' + str(size_payload) + '\n' + \
                          'time: ' + str(time_tr) + '\n' + \
                          'video data rate: ' + str(int(size_payload) // time_tr) + ' bytes/s\n')

                    currFrameNbr = rtpPacket.seqNum()
                    print("Current Seq Num: " + str(currFrameNbr))

                    # Set time box
                    currentTime = int(currFrameNbr * 0.05)
                    self.timeBox = str(currentTime // 60) + " : " + str(currentTime % 60)
                    self.status = Label(self.master, text="Watched time : " + str(self.timeBox), bd=1, relief=SUNKEN,
                                        anchor=W)
                    self.status.grid(row=2, column=0, columnspan=1, sticky=W + E)

                    if currFrameNbr > self.frameNbr:  # Discard the late packet
                        self.frameNbr = currFrameNbr
                        self.updateMovie(self.writeFrame(rtpPacket.getPayload()))
            except:
                # Stop listening upon requesting PAUSE or TEARDOWN
                if self.playEvent.isSet():
                    break

                # Upon receiving ACK for TEARDOWN request,
                # close the RTP socket
                if self.teardownAcked == 1 or self.stoped == 1:
                    self.rtpSocket.shutdown(socket.SHUT_RDWR)
                    self.rtpSocket.close()
                    break

    def writeFrame(self, data):
        """Write the received frame to a temp image file. Return the image file."""
        cachename = CACHE_FILE_NAME + str(self.sessionId) + CACHE_FILE_EXT
        file = open(cachename, "wb")
        file.write(data)
        file.close()

        return cachename

    def updateMovie(self, imageFile):
        """Update the image file as video frame in the GUI."""
        photo = ImageTk.PhotoImage(Image.open(imageFile))
        self.label.configure(image=photo, height=288)
        self.label.image = photo

    def connectToServer(self):
        """Connect to the Server. Start a new RTSP/TCP session."""
        self.rtspSocket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        try:
            self.rtspSocket.connect((self.serverAddr, self.serverPort))


        except:
            tkinter.messagebox.showwarning('Connection Failed', 'Connection to \'%s\' failed.' % self.serverAddr)

    def sendRtspRequest(self, requestCode):
        """Send RTSP request to the server."""
        # -------------
        # TO COMPLETE
        # -------------

        # Setup request
        if requestCode == self.SETUP and self.state == self.INIT:
            threading.Thread(target=self.recvRtspReply).start()

            self.rtspSeq += 1

            # Write the RTSP request to be sent.
            request = 'SETUP' + ' ' + self.fileName + " RTSP/1.0\n"
            request = request + ("CSeq: %d\n" % self.rtspSeq)
            request = request + "Transport: RTP/UDP; client_port= %d\n" % (self.rtpPort)

            # Keep track of the sent request.
            self.requestSent = self.SETUP

        # Play request
        elif requestCode == self.PLAY and self.state == self.READY:

            self.rtspSeq += 1

            # Write the RTSP request to be sent.
            request = 'PLAY' + ' ' + self.fileName + ' RTSP/1.0\n'
            request = request + ("CSeq: %d\n" % self.rtspSeq)
            request = request + "Transport: RTP/UDP; client_port= %d\n" % (self.rtpPort)

            # Keep track of the sent request.
            self.requestSent = self.PLAY

        # Pause request
        elif requestCode == self.PAUSE and self.state == self.PLAYING:

            self.rtspSeq += 1

            # Write the RTSP request to be sent.
            request = 'PAUSE' + ' ' + self.fileName + ' RTSP/1.0\n'
            request = request + ("CSeq: %d\n" % self.rtspSeq)
            request = request + "Transport: RTP/UDP; client_port= %d\n" % (self.rtpPort)

            # Keep track of the sent request.
            self.requestSent = self.PAUSE

        # Teardown request
        elif requestCode == self.TEARDOWN and not self.state == self.INIT:

            self.rtspSeq += 1

            # Write the RTSP request to be sent.
            request = 'TEARDOWN' + ' ' + self.fileName + ' RTSP/1.0\n'
            request = request + ("CSeq: %d\n" % self.rtspSeq)
            request += "Session: %d\n" % self.sessionId
            # Keep track of the sent request.
            self.requestSent = self.TEARDOWN

        # Stop request
        elif requestCode == self.STOP and not self.state == self.INIT:
            self.rtspSeq += 1
            self.state = self.INIT
            self.stop = 1
            # Write the RTSP request to be sent.
            request = 'STOP' + ' ' + self.fileName + ' RTSP/1.0\n'
            request = request + ("CSeq: %d\n" % self.rtspSeq)
            request = request + "Transport: RTP/UDP; client_port= %d\n" % (self.rtpPort)
            self.requestSent = self.STOP

            # Update time box
            self.timeBox = "0 : 0"
            self.status = Label(self.master, text="Watched time : " + str(self.timeBox), bd=1, relief=SUNKEN,
                                anchor=W)
            self.status.grid(row=2, column=0, columnspan=1, sticky=W + E)

        # Describe request
        elif requestCode == self.DESCRIBE:
            self.rtspSeq += 1
            request = 'DESCRIBE' + ' ' + self.fileName + ' RTSP/1.0\n'
            request = request + ("CSeq: %d\n" % self.rtspSeq)
            request = request + "Transport: RTP/UDP; client_port= %d\n" % (self.rtpPort)
            self.requestSent = self.DESCRIBE

        # Describe request
        elif requestCode == self.SWITCH:
            self.rtspSeq += 1
            self.state = self.INIT
            self.stop = 1

            # Switch video
            if self.video_list_index < len(self.video_list) - 1:
                self.video_list_index += 1
            else:
                self.video_list_index = 0
            self.fileName = self.video_list[self.video_list_index]

            request = 'SWITCH' + ' ' + self.fileName + ' RTSP/1.0\n'
            request = request + ("CSeq: %d\n" % self.rtspSeq)
            request = request + "Transport: RTP/UDP; client_port= %d\n" % (self.rtpPort)
            self.requestSent = self.SWITCH

            # Update time box
            self.timeBox = "0 : 0"
            self.status = Label(self.master, text="Watched time : " + str(self.timeBox), bd=1, relief=SUNKEN,
                                anchor=W)
            self.status.grid(row=2, column=0, columnspan=1, sticky=W + E)

        else:
            return

        # Send the RTSP request using rtspSocket.
        # ...
        self.rtspSocket.sendall(request.encode())
        print('\nData sent:\n' + request)

    def recvRtspReply(self):
        """Receive RTSP reply from the server."""
        while True:
            reply = self.rtspSocket.recv(1024)

            if reply:
                self.parseRtspReply(reply.decode("utf-8"))

            # Close the RTSP socket upon requesting Teardown
            # if self.requestSent == self.TEARDOWN:
            if self.teardownAcked == 1:
                self.rtspSocket.shutdown(socket.SHUT_RDWR)
                self.rtspSocket.close()
                break

    def parseRtspReply(self, data):
        """Parse the RTSP reply from the server."""
        lines = data.split('\n')
        seqNum = int(lines[1].split(' ')[1])

        # Process only if the server reply's sequence number is the same as the request's
        if seqNum == self.rtspSeq:
            session = int(lines[2].split(' ')[1])
            # New RTSP session ID
            if self.sessionId == 0:
                self.sessionId = session

            # Process only if the session ID is the same
            if self.sessionId == session:
                if int(lines[0].split(' ')[1]) == 200:
                    if self.requestSent == self.SETUP:
                        # -------------
                        # TO COMPLETE
                        # -------------
                        # Update RTSP state.
                        # self.state = ...
                        self.state = self.READY
                        # Open RTP port.
                        self.openRtpPort()
                    elif self.requestSent == self.PLAY:
                        # self.state = ...
                        self.state = self.PLAYING
                    elif self.requestSent == self.PAUSE:
                        # self.state = ...
                        self.state = self.READY
                        # The play thread exits. A new thread is created on resume.
                        self.playEvent.set()
                    elif self.requestSent == self.TEARDOWN:
                        self.state = self.INIT
                        # Flag the teardownAcked to close the socket.
                        self.teardownAcked = 1
                    elif self.requestSent == self.STOP:
                        # self.label.image=None
                        self.frameNbr = 0
                        self.rtspSeq = 0
                        # self.playEvent.set()
                        self.stoped = 1
                    elif self.requestSent == self.DESCRIBE:
                        # print str(data)
                        # cachename = CACHE_FILE_NAME + str(self.sessionId) + '.txt'
                        # file = open(cachename, "w")
                        # file.write(str(lines[3]) + '\n' + str(lines[4])+'\nSize of Video: '+str(lines[5])+' bytes')
                        print(data + '\n')
                    elif self.requestSent == self.SWITCH:
                        # Stop first
                        self.frameNbr = 0
                        self.rtspSeq = 0
                        self.stoped = 1

    def openRtpPort(self):
        """Open RTP socket binded to a specified port."""

        self.rtpSocket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        # Set the timeout value of the socket to 0.5sec
        self.rtpSocket.settimeout(0.5)

        try:
            # Bind the socket to the address using the RTP port given by the client user
            self.state = self.READY
            self.rtpSocket.bind(('', self.rtpPort))
        except:
            tkinter.messagebox.showwarning('Unable to Bind', 'Unable to bind PORT=%d' % self.rtpPort)

    def handler(self):
        """Handler on explicitly closing the GUI window."""
        self.pauseMovie()
        if tkinter.messagebox.askokcancel("Quit?", "Are you sure you want to quit?"):
            self.exitClient()
        else:  # When the user presses cancel, resume playing.
            self.playMovie()
