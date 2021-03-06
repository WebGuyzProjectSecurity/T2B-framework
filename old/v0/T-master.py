#!/usr/bin/env python
import select, socket, sys, threading, subprocess, os, time, hmac, hashlib, datetime
from colored import fg, bg, attr
from subprocess import check_output
from Crypto.Cipher import AES

pid = subprocess.Popen(args=["xterm","-e","./net.py"]).pid # numb. of real time connected client

class PKCS7Encoder():
    class InvalidBlockSizeError(Exception):
        """Raised for invalid block sizes"""
        pass

    def __init__(self, block_size=16):
        if block_size < 2 or block_size > 255:
            raise PKCS7Encoder.InvalidBlockSizeError('The block size must be ' \
                    'between 2 and 255, inclusive')
        self.block_size = block_size

    def encode(self, text):
        text_length = len(text)
        amount_to_pad = self.block_size - (text_length % self.block_size)
        if amount_to_pad == 0:
            amount_to_pad = self.block_size
        pad = chr(amount_to_pad)
        return text + pad * amount_to_pad

    def decode(self, text):
        pad = ord(text[-1])
        return text[:-pad]

encoder = PKCS7Encoder()

def Upload(fileName):
		file_input = open(fileName, 'rb')
		size = str(os.stat(fileName).st_size)
		SendTextCipher(size)
		SendTextCipher(fileName)
		while 1:
			Exec("clear")
			print "Uploading: " + " " + fileName 
			print "Started at " + str(datetime.datetime.now())
			bb = file_input.read(256)
			if bb == "": break
			SendTextCipher(bb)
			waiting = RecvTextCipher()
		file_input.close()
		SendTextCipher("upload_server_close")

def Download(fileName):
		file_input = open(fileName, 'wa')
		size = RecvTextCipher()
		while 1:
			Exec("clear")
			print "Downloading: " + " " + fileName 
			print "Started at " + str(datetime.datetime.now())
			SendTextCipher(os.urandom(10))
			bb = RecvTextCipher()
			if bb == "upload_client_close": break
			file_input.write(bb)
		file_input.close()

def ExecIN(cmd):
		out = check_output(cmd, shell=True)
		print out

def CheckHash(check):
		HM = hmac.new(key, check[:-32], hashlib.sha256)
		if hmac.compare_digest(HM.digest(), check[-32:]) == True:
			pas = 1 + 5
		else:
			print "error"
			
def Encrypt(clearData):
		encryptor = cipher
		padded_data = encoder.encode(clearData)
		chiper_t = encryptor.encrypt(padded_data)
		return chiper_t
      
def Decrypt(cipherData):
		decryptor = cipher
		de_chiper_t = decryptor.decrypt(cipherData)
		unpadded_data = encoder.decode(de_chiper_t)
		return unpadded_data

iv = os.urandom(16)
key = ',U\x10\xab\xf6\xc6D\x08\xa7\xb7\xa36\xd6\t\x12\xaa'
zero = "zero"
cipher = AES.new(key, AES.MODE_CBC, iv)
print "%s---------------------------%s" % (fg(46), attr(0))
print "%s[Starting server]%s" % (fg(46), attr(0))

class Server:
	def __init__(self):
		self.host = 'localhost'
		self.port = 5555
		self.backlog = 5
		self.size = 4096
		self.server = None
		self.threads = []

	def open_socket(self):
		try:
			self.server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
			self.server.bind((self.host,self.port))
			self.server.listen(5)
			print "%s---------------------------%s" % (fg(46), attr(0))
			print "%s%s[server-status] ok.%s" % (fg(46), attr(1), attr(0))
			print "%s---------------------------%s" % (fg(46), attr(0))
			print ("%s[server-key] " + key.encode("hex")+"%s") % (fg(46), attr(0))
			print ("%s[server-infos] " + str(self.host) + ":" + str(self.port) + "%s") % (fg(46), attr(0))
			print ("%s[server-infos] backlog: " + str(self.backlog) + "%s") % (fg(46), attr(0))
			print "%s---------------------------%s" % (fg(46), attr(0))
			print "%s...waiting...%s" % (fg(46), attr(0))
		except socket.error, (value,message):
			if self.server:
				self.server.close()
				print ("%sCould not open socket: " + message + "!!%s") % (fg(196), attr(0))
				sys.exit(1)

	def run(self):
		self.open_socket()
		input = [self.server,sys.stdin]
		running = 1
		while running:
			inputready,outputready,exceptready = select.select(input,[],[])
			for s in inputready:
				if s == self.server:
					# handle the server socket
					c = Client(self.server.accept())
					c.start()
					self.threads.append(c)
				else:
					running = 0 
					break
		self.server.close()
		for c in self.threads:
			c.join()

class Client(threading.Thread):
	def __init__(self,(client,address)):
		threading.Thread.__init__(self)
		self.client = client
		self.address = address
		self.size = 4096
		threading.current_thread()
	
	def RecvTextCipher(self):
		l1 = self.client.recv(self.size)
		l = Decrypt(l1)
		data = "" 
		while(l):
			data += l
			if data.endswith(zero) == True :
				break
			else :
				l1 = self.client.recv(self.size)
				l = Decrypt(l1)
		endback = len(zero) + 32
		#print "Recv: " + data[:-endback]
		CheckHash(data[:-len(zero)])
		return data[:-endback]
	
	def SendTextCipher(self,info2):
		HM1 = hmac.new(key, info2, hashlib.sha256)
		info1 = info2 + HM1.digest() + zero
		info = Encrypt(info1)
		self.client.sendall(info)
	
	def SendTextClear(self,info):
		HM2 = hmac.new(key, info, hashlib.sha256)
		info1 = info + HM2.digest() + zero
		self.client.sendall(info1)

	def run(self):
		running = 1
		self.SendTextClear(iv)
		while running:
			try:
				inText = self.RecvTextCipher()
				#string = str(threading.current_thread()).split(" ")
				if inText.split(" ")[2] == "terminate":
					print ("%s------["+ str(threading.current_thread()).split(" ")[2][:len(str(threading.current_thread()).split(" ")[2])-2] + "]---"+ str(self.address) + " == " +inText.split(" ")[0] +" [terminated]%s") % (fg(202), attr(0))
					self.client.close()
					running = 0
				else:
					self.SendTextCipher(inText)
					print ("%s---[" + str(threading.current_thread()).split(" ")[2][:len(str(threading.current_thread()).split(" ")[2])-2] + "]---" + str(self.address) + " == " + inText + "%s") % (fg(45), attr(0))
			except socket.error:
				self.client.close()
				running = 0

s = Server()
s.run()

