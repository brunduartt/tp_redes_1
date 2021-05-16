import math
import os
import random
import socket
from enum import Enum
from tkinter import *
from _thread import *
import threading

from answer_code_enum import AnswerCode
from fuel_type_enum import *
from fuel_station import *
from utils import parseToStation


class Server:

    def __init__(self):
        self.dbFilePath = "db.txt"
        self.print_lock = threading.Lock()
        self.HOST = '127.0.0.1'
        self.stations = []
        self.PORT = 7777
        self.isHosting = False
        self.loadDb()
        self.root = Tk()
        self.root.title("TP - Sistema de Preços - Servidor")
        self.root.geometry("200x100")
        self.portInputValue = StringVar()
        portRow = Frame(self.root)
        Label(portRow, width=15, text="Porta", anchor='w').pack(side=LEFT)
        Entry(portRow, textvariable=self.portInputValue).pack(side=RIGHT, expand=YES, fill=X)
        portRow.pack(side=TOP, fill=X, padx=5, pady=5)
        self.hostButton = Button(self.root, text="Hostear", command=self.confirm)
        self.hostButton.pack(side=TOP, expand=YES)
        self.root.mainloop()

    def checkIfElementAtArea(self, element, lat, lon, radius):
        distance = math.sqrt(math.pow(element.lat - lat, 2) + math.pow(element.lon - lon, 2))
        if distance > radius:
            return False
        else:
            return True

    def smallestPrice(self, elem):
        return elem.price

    def confirm(self):
        if (not self.isHosting) and self.portInputValue.get():
            self.PORT = int(self.portInputValue.get())
            self.hostButton.configure(text="Carregando...")
            self.start()

    def loadDb(self):
        try:
            f = open(self.dbFilePath, "r")
            lines = f.readlines()
            for line in lines:
                fuelTypeStr, latStr, lonStr, priceStr = line.split(',')
                if fuelTypeStr != "" and latStr != "" and lonStr != "" and priceStr != "":
                    self.stations.append(parseToStation(fuelTypeStr, latStr, lonStr, priceStr))
        except IOError:
            print("Erro ao acessar arquivo")
        finally:
            f.close()

    def addStation(self, fuelTypeStr, latStr, lonStr, priceStr):
        try:
            f = open(self.dbFilePath, "a+")
            self.stations.append(parseToStation(fuelTypeStr, latStr, lonStr, priceStr))
            f.write(fuelTypeStr+","+latStr+","+lonStr+","+priceStr+"\n")
            return str(AnswerCode.CREATED.value)
        except IOError:
            print("Erro ao acessar arquivo")
            return str(AnswerCode.BAD_REQUEST.value)
        finally:
            f.close()

    def searchDb(self, fuelType, lat, lon, radius):
        list = [x for x in self.stations if x.fuelType == fuelType and self.checkIfElementAtArea(x, lat, lon, radius)]
        if len(list) > 0:
            list.sort(key=self.smallestPrice)
            elementLat = str(list[0].lat)
            elementLon = str(list[0].lon)
            return str(AnswerCode.OK.value)+","+str(list[0].fuelType.value)+","+elementLat+","+elementLon+","+str(list[0].price)
        else:
            return str(AnswerCode.NOT_FOUND.value)

    def processMessage(self, udp, address, msg):
        print("Menssagem:", msg)
        print("Endereço:", address)
        msgType = msg[0]
        if msgType == "D":
            msgType, fuelTypeStr, latStr, lonStr, priceStr = msg.split(',')
            returnMsg = self.addStation(fuelTypeStr, latStr, lonStr, priceStr)
        elif msgType == "P":
            msgType, fuelTypeStr, latStr, lonStr, radiusStr = msg.split(',')
            returnMsg = self.searchDb(FuelType(int(fuelTypeStr)), float(latStr), float(lonStr), int(radiusStr))
        elif msgType == "T":
            returnMsg = str(AnswerCode.ACCEPTED.value)
        else:
            returnMsg = str(AnswerCode.BAD_REQUEST.value)
        udp.sendto(str.encode(returnMsg), address)

    def udp_thread(self, udp):
        while True:
            msg, address = udp.recvfrom(1024)
            if msg and address:
                start_new_thread(self.processMessage, (udp, address, msg.decode()))


    def start(self):
        udp = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        udp.bind((self.HOST, self.PORT))
        self.hostButton.configure(text="Hosteando")
        self.isHosting = True
        self.print_lock.acquire()
        start_new_thread(self.udp_thread, (udp,))

Server()