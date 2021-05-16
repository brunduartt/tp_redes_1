#!/usr/bin/env python3
import threading
from _thread import start_new_thread
from enum import Enum
from tkinter import *
from functools import partial
import socket

from answer_code_enum import AnswerCode
from fuel_type_enum import FuelType


def rgbtohex(r,g,b):
    return f'#{r:02x}{g:02x}{b:02x}'

class ClientState(Enum):
    WAITING_CONNECTION = 0
    SETTING_PLAYER_SHIPS = 1
    PLAYING = 2,
    END = 3

CONNECT_COMMAND_INDEX = 1
ADD_COMMAND_INDEX = 2
SEARCH_COMMAND_INDEX = 3

class SearchOrAddStationWindow(Toplevel):

    def show(self):
        self.wm_deiconify()
        self.latEntry.focus_force()
        self.wait_window()
        return self.fuelTypeVar.get(), self.latInputValue.get(), self.lonInputValue.get(), self.priceOrRadiusInputValue.get()

    def confirm(self, event=None):
        self.destroy()

    def __init__(self, master=None, isSearch=False):
        super().__init__(master=master)
        self.isSearch = isSearch
        title = "Pesquisar" if self.isSearch else "Adicionar"
        self.title(title)
        self.geometry("200x250")
        self.fuelTypeVar = IntVar()
        self.fuelTypeVar.set(FuelType.DIESEL.value)
        fuelTypeFrame = Frame(self)
        Radiobutton(fuelTypeFrame, text="0 - Diesel", variable=self.fuelTypeVar, value=FuelType.DIESEL.value).pack(anchor=W)
        Radiobutton(fuelTypeFrame, text="1 - Álcool", variable=self.fuelTypeVar, value=FuelType.ALCOHOL.value).pack(anchor=W)
        Radiobutton(fuelTypeFrame, text="2 - Gasolina", variable=self.fuelTypeVar, value=FuelType.GAS.value).pack(anchor=W)
        fuelTypeFrame.pack(side=TOP, fill=X, padx=5, pady=5)

        self.latInputValue = StringVar()
        latRow = Frame(self)
        Label(latRow, width=15, text="Lat", anchor='w').pack(side=LEFT)
        self.latEntry = Entry(latRow, textvariable=self.latInputValue)
        latRow.pack(side=TOP, fill=X, padx=5, pady=5)
        self.latEntry.pack(side=RIGHT, expand=YES, fill=X)

        self.lonInputValue = StringVar()
        lonRow = Frame(self)
        Label(lonRow, width=15, text="Lon", anchor='w').pack(side=LEFT)
        Entry(lonRow, textvariable=self.lonInputValue).pack(side=RIGHT, expand=YES, fill=X)
        lonRow.pack(side=TOP, fill=X, padx=5, pady=5)

        self.priceOrRadiusInputValue = StringVar()
        priceOrRadiusRow = Frame(self)
        Label(priceOrRadiusRow, width=15, text=("Raio" if self.isSearch else "Preço"), anchor='w').pack(side=LEFT)
        Entry(priceOrRadiusRow, textvariable=self.priceOrRadiusInputValue).pack(side=RIGHT, expand=YES, fill=X)
        priceOrRadiusRow.pack(side=TOP, fill=X, padx=5, pady=5)

        Button(self, text=title, command=self.confirm).pack(side=TOP, expand=YES)

class ConnectWindow(Toplevel):

    def show(self):
        self.wm_deiconify()
        self.ipEntry.focus_force()
        self.wait_window()
        return self.ipInputValue.get(), self.portInputValue.get()

    def confirm(self, event=None):
        self.destroy()

    def __init__(self, master=None):
        super().__init__(master=master)
        self.title("Endereço do Servidor")
        self.geometry("200x100")

        self.ipInputValue = StringVar()
        ipRow = Frame(self)
        Label(ipRow, width=15, text="IP", anchor='w').pack(side=LEFT)
        self.ipEntry = Entry(ipRow, textvariable=self.ipInputValue)
        ipRow.pack(side=TOP, fill=X, padx=5, pady=5)
        self.ipEntry.pack(side=RIGHT, expand=YES, fill=X)

        self.portInputValue = StringVar()
        portRow = Frame(self)
        Label(portRow, width=15, text="Porta", anchor='w').pack(side=LEFT)
        Entry(portRow, textvariable=self.portInputValue).pack(side=RIGHT, expand=YES, fill=X)
        portRow.pack(side=TOP, fill=X, padx=5, pady=5)

        Button(self, text="Conectar", command=self.confirm).pack(side=TOP, expand=YES)


class Client:

    def __init__(self):
        self.print_lock = threading.Lock()
        self.maxSendAttempt = 5
        self.root = Tk()
        self.id = 0
        self.port = None
        self.ip = None
        self.logLabelVar = StringVar()
        self.logLabelVar1 = StringVar()
        self.logLabelVar2 = StringVar()
        self.root.title("TP - Sistema de Preços")
        self.root.geometry("300x300")
        self.logLabelFrame = Frame(self.root)
        self.logLabelFrame.pack(side=BOTTOM, expand=True)
        self.logLabel = Label(self.logLabelFrame, textvariable=self.logLabelVar).pack(side=TOP, expand=True)
        self.logLabel1 = Label(self.logLabelFrame, textvariable=self.logLabelVar1).pack(side=TOP, expand=True)
        self.logLabel2 = Label(self.logLabelFrame, textvariable=self.logLabelVar2).pack(side=TOP, expand=True)
        self.print_lock.acquire()
        # menu.add_command(label="Reiniciar", command=Restart, state=ENABLED if isConnected else DISABLED)
        # menu.add_command(label="Sair", command=Quit)

    def address(self):
        self.ip, port = ConnectWindow().show()
        if not self.ip:
            self.ip = "127.0.0.1"
        if not port:
            self.port = 7777
        else:
            self.port = int(port)
        self.sendMessage("T")

    def decodeAnswer(self, answer):
        args = answer.split(',')
        code = AnswerCode(int(args[0]))
        if code is AnswerCode.OK:
            fuelType = FuelType(int(args[1]))
            if fuelType is FuelType.GAS:
                fuelTypeDesc = "Álcool"
            elif fuelType is FuelType.DIESEL:
                fuelTypeDesc = "Diesel"
            else:
                fuelTypeDesc = "Gasolina"
            lat = args[2]
            lon = args[3]
            price = float(args[4])/1000
            self.logLabelVar.set("Posto de combustível encontrado.\nTipo: "+str(fuelType.value) + " - " + fuelTypeDesc + "\nLatitude: " + lat + "\nLongitude: " + lon + "\nPreço: " + str(price))
        elif code is AnswerCode.CREATED:
            self.logLabelVar.set("Posto de Combustível criado!")
        elif code is AnswerCode.NOT_FOUND:
            self.logLabelVar.set("Não foi encontrado nenhum posto na área especificada.")
        elif code is AnswerCode.ACCEPTED:
            self.logLabelVar.set("Conexão realizada.")
        elif code is AnswerCode.BAD_REQUEST:
            self.logLabelVar.set("Erro ao criar Posto de Combustível!")
        else:
            self.logLabelVar.set("Resposta inválida")

    def sendMessageThread(self, messageBytes, socket):
        attempt = 0
        sentMessage = False
        self.logLabelVar.set("Enviando...")
        self.disableMethodsMenu()
        while (not sentMessage) and (attempt < self.maxSendAttempt):
            try:
                socket.sendto(messageBytes, (self.ip, self.port))
                socket.settimeout(2)
                bytes, address = socket.recvfrom(1024)
                answer = bytes.decode()
                self.decodeAnswer(answer)
                self.enableMethodsMenu()
                print('Resposta: ', repr((bytes, address)))
                sentMessage = True
                socket.close()
                attempt += 1
            except:
                print("Falha na Requisição")
                sentMessage = False
                attempt += 1
                self.logLabelVar.set(("Enviando... (" + str(attempt) + ")"))

        if not sentMessage:
            self.disableMethodsMenu()
            self.logLabelVar.set("Falha no Envio")


    def sendMessage(self, message):
        sendSocket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        messageBytes = str.encode(message)
        start_new_thread(self.sendMessageThread, (messageBytes, sendSocket))

    def search(self):
        fuelType, latStr, lonStr, radiusStr = SearchOrAddStationWindow(isSearch=True).show()
        if fuelType != "" and latStr != "" and lonStr != "" and radiusStr != "":
            radiusStr = radiusStr.replace(',', '.')
            self.sendMessage('P,'+str(fuelType)+","+latStr+","+lonStr+","+radiusStr)

    def add(self):
        fuelType, latStr, lonStr, priceStr = SearchOrAddStationWindow().show()
        if fuelType != "" and latStr != "" and lonStr != "" and priceStr != "":
            priceStr = priceStr.replace(',', '.')
            priceStr = str(int((float(priceStr)*1000)))
            self.sendMessage('D,'+str(fuelType)+","+latStr+","+lonStr+","+priceStr)

    def disableMethodsMenu(self):
        self.menu.entryconfig(SEARCH_COMMAND_INDEX, state=DISABLED)
        self.menu.entryconfig(ADD_COMMAND_INDEX, state=DISABLED)

    def enableMethodsMenu(self):
        self.menu.entryconfig(SEARCH_COMMAND_INDEX, state=ACTIVE)
        self.menu.entryconfig(ADD_COMMAND_INDEX, state=ACTIVE)

    def show(self):
        # ---- Métodos menu -------
        self.menu = Menu(self.root)
        self.menu.add_command(label="Endereço", command=self.address)
        self.menu.add_command(label="Pesquisar", command=self.search)
        self.menu.add_command(label="Adicionar", command=self.add)
        self.disableMethodsMenu()
        self.root.config(menu=self.menu)
        self.root.mainloop()


Client().show()
