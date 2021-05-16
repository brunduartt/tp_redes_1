import random
import socket
from ship_type_enum import *
from orientation_enum import *
from tkinter import *
from _thread import *
import threading

class ServerState(Enum):
    WAITING_START_HOST = 0
    WAITING_CONNECTION = 1
    WAITING_PLAYER_SHIPS = 2
    PLAYING = 3
    END = 4



class Server:

    def show(self):
        self.menu.add_command(label="Conectar", command=self.connect)
        self.root.config(menu=self.menu)
        self.root.mainloop()

    def __init__(self):
        self.print_lock = threading.Lock()
        self.HOST = '127.0.0.1'
        self.PORT = 7777
        self.serverBoard = None
        self.playerBoard = None
        self.clientsocket = None
        self.amountShips = None
        self.playerBoardChecks = None
        self.state = ServerState.WAITING_START_HOST
        self.root = Tk()
        self.root.title("TP - Batalha Naval - Servidor")
        self.root.geometry("200x100")
        self.portInputValue = StringVar()
        portRow = Frame(self.root)
        Label(portRow, width=15, text="Porta", anchor='w').pack(side=LEFT)
        Entry(portRow, textvariable=self.portInputValue).pack(side=RIGHT, expand=YES, fill=X)
        portRow.pack(side=TOP, fill=X, padx=5, pady=5)
        self.hostButton = Button(self.root, text="Hostear", command=self.confirm)
        self.hostButton.pack(side=TOP, expand=YES)
        self.root.mainloop()

    def confirm(self):
        if self.state == ServerState.WAITING_START_HOST and self.portInputValue.get(): #se esperando conexão com servidor e campo de porta com valor
            self.PORT = int(self.portInputValue.get())
            self.hostButton.configure(text="Carregando...")
            self.start()

    def checkIfShipAtPositions(self, x, y, size, orientation):
        incX = 0
        incY = 0

        if orientation == Orientation.VERTICAL:
            incY = 1
        else:
            incX = 1
        for i in range(0, size):
            if self.serverBoard[y + (incY*i)][x + (incX*i)]: #checa se já há um navio ocupando a posição especificada + o tamanho do navio na orientação especificada
                return False
        return True

    def placeShipAtRandomPosition(self, type):
        incX = 0
        incY = 0
        randX = 0
        randY = 0
        valid = False
        size = type.value
        while(not valid): #enquanto não for uma posição válida
            orientationRandom = random.randint(1, 2)
            orientation = Orientation.HORIZONTAL
            incX = 0
            incY = 0
            if orientationRandom == 2: #decide se o navio estará na posição vertical ou horizontal
                incY = 1
                orientation = Orientation.VERTICAL
            else:
                incX = 1
            randX = random.randint(0, 9 - (size * incX)) #subtração no 9 pois o navio nunca estará acima da posição 9 do eixo correspondente a sua orientação
            randY = random.randint(0, 9 - (size * incY))
            valid = self.checkIfShipAtPositions(randX, randY, type.value, orientation) #checa se posição válida
        for i in range(0, size): #marca da posição encontrada até o tamanho do tipo de navio
            self.serverBoard[randY + (incY*i)][randX + (incX*i)] = True


    def initServerBoard(self):
        random.seed()
        self.serverBoard = [[False for x in range(10)] for y in range(10)]
        self.playerBoardChecks = [[False for x in range(10)] for y in range(10)] #entidade para marcar as posição do tabuleiro do jogador que o servidor tentou acertar
        self.amountShips = { #inicializa com a quantidade de cada tipo de navio
            ShipType.AIRCRAFT_CARRIER: 1,
            ShipType.TANKER: 2,
            ShipType.DESTROYER: 3,
            ShipType.SUBMARINE: 4,
        }
        for key, value in self.amountShips.items():
            for i in range(value): #coloca cada navio em uma posição aleatória válida
                self.placeShipAtRandomPosition(key)

    def initPlayerBoard(self, byteStr):
        self.playerBoard = [[False for x in range(10)] for y in range(10)] #inicializa tabuleiro do jogador no servidor
        for y in range(0, 10):
            for x in range(10):
                print((y*10)+x)
                print(len(byteStr))
                if byteStr[(y*10)+x] == "1": #marca toda posição que possui um navio com True
                    self.playerBoard[y][x] = True
        print(self.playerBoard)

    def checkIfServerLost(self):
        end = True
        for x in range(10):
            for y in range(10):
                if self.serverBoard[y][x]: #se tiver ainda alguma posição com True, significa que ainda tem posições com navios que não foram verificadas
                    end = False
                    break
            if not end:
                break
        return end

    def checkIfPlayerLost(self):
        end = True
        for x in range(10):
            for y in range(10):
                if self.playerBoard[y][x]: #se tiver ainda alguma posição com True, significa que ainda tem posições com navios que não foram verificadas
                    end = False
                    break
            if not end:
                break
        return end

    # Formato de resposta:
      # {serverBoardHit, serverLost, playerBoardHit, playerLost, xServer, yServer}
    def checkIfHit(self, x, y):
        returnStr = ""
        if self.serverBoard[y][x]: #se tabuleiro do servidor possui um navio na posição, retorna True
            returnStr += "True,"
            self.serverBoard[y][x] = False
            serverLost = self.checkIfServerLost() #checa se o servidor não possui mais posições, com navios, que não foram acertadas
            if(serverLost): #se não tiver, servidor perdeu
                returnStr += "True,"
                self.state = ServerState.END
            else:
                returnStr += "False,"
        else: #se não possuir navio na posição, retorna False
            returnStr += "False,False,"

        validPosition = False
        while not validPosition: #seleciona uma posição aleatória do tabuleiro do jogador que ainda não foi verificada
            x = random.randint(0, 9)
            y = random.randint(0, 9)
            if not self.playerBoardChecks[y][x]:
                validPosition = True
        self.playerBoardChecks[y][x] = True #marca posição como verificada
        if(self.playerBoard[y][x]): #retorna True se jogador possui navio na posição
            returnStr += "True,"
            self.playerBoard[y][x] = False
            playerLost = self.checkIfPlayerLost() #checa se o jogador não possui mais posições, com navios, que não foram acertadas
            if(playerLost): #se não tiver, jogador perdeu
                returnStr += "True,"
                self.state = ServerState.END
            else:
                returnStr += "False,"
        else: #se não possuir navio na posição, retorna False
            returnStr += "False,False,"

        returnStr += str(x) + ',' + str(y) #retorna posição que o servidor tentou acertar

        self.clientsocket.sendall(str.encode(returnStr))

    def deciferByteStr(self, byteStr):
        print("Message:", byteStr)
        if self.state == ServerState.WAITING_CONNECTION: #se servidor esperava conexão pelo cliente
            self.clientsocket.sendall(b'Conectado.')
            self.state = ServerState.WAITING_PLAYER_SHIPS
        elif self.state == ServerState.WAITING_PLAYER_SHIPS: #se servidor esperando posições dos navios do jogador
            self.initPlayerBoard(byteStr)
            self.initServerBoard()
            self.state = ServerState.PLAYING
        elif self.state == ServerState.PLAYING: #se servidor esperando posição de tiro do jogador
            xStr, yStr = byteStr.split(',')
            self.checkIfHit(int(xStr), int(yStr))

    def listen_thread(self, tcp):
        while True:
            (self.clientsocket, address) = tcp.accept() #Espera receber uma requisição
            print('Conectado à ' + str(address))
            self.hostButton.configure(text='Conectado à ' + str(address))
            while True: #Continua escutando enquanto ao socket até não receber mais nada
                msg = self.clientsocket.recv(1024)
                if not msg:
                    break
                self.deciferByteStr(msg.decode())
            print("Finalizada conexão com", address)
            self.clientsocket.close()
            self.state = ServerState.WAITING_CONNECTION
            self.hostButton.configure(text="Esperando Conexão")


    def start(self):
        print(self.PORT)
        tcp = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        tcp.bind((self.HOST, self.PORT))
        self.hostButton.configure(text="Esperando Conexão")
        self.state = ServerState.WAITING_CONNECTION
        tcp.listen(1) #Aceita apenas 1 conexão por vez
        self.print_lock.acquire()
        start_new_thread(self.listen_thread, (tcp,)) #Nova thread para ficar responsável por escutar as requisições

Server()