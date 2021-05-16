#!/usr/bin/env python3
from enum import Enum
from tkinter import *
from functools import partial
from ship_type_enum import *
from orientation_enum import *
import socket

def rgbtohex(r,g,b):
    return f'#{r:02x}{g:02x}{b:02x}'

class ClientState(Enum):
    WAITING_CONNECTION = 0
    SETTING_PLAYER_SHIPS = 1
    PLAYING = 2,
    END = 3

class Grid(Enum):
    PLAYER = 0
    SERVER = 1
    VISUALIZE = 2

ShipTypeColor = {
    ShipType.AIRCRAFT_CARRIER: rgbtohex(171, 171, 171),
    ShipType.TANKER:  rgbtohex(140, 140, 140),
    ShipType.DESTROYER: rgbtohex(110, 110, 110),
    ShipType.SUBMARINE:  rgbtohex(80, 80, 80),
}

CONNECT_COMMAND_INDEX = 1

class Ship:
    def __init__(self, id):
        self.x = 0
        self.id = id
        self.y = 0
        self.type = None
        self.orientation = Orientation.HORIZONTAL

    def setShipPosition(self, x, y, orientation=Orientation.HORIZONTAL):
        self.x = x
        self.y = y
        self.orientation = orientation

    def setShipType(self, type):
        self.type = type


class GridCell:
    def __init__(self, x, y, button):
        self.button = button
        self.x = x
        self.y = y
        self.ship = None
        self.hit = False
        self.checked = False


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
        self.title("Conectar")
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

    def changeMenuState(self):
        print(self.isConnected)
        self.menu.entryconfig(CONNECT_COMMAND_INDEX, state=DISABLED if self.isConnected else NORMAL)
        # self.menu.entryconfig(RESET_COMMAND_INDEX, state=NORMAL if self.isConnected else DISABLED)

    def resetShipInitParams(self):
        self.id = 0
        self.shipInitOrientation = IntVar()
        self.shipInitOrientation.set(Orientation.HORIZONTAL.value)
        self.shipInitType = ShipType.AIRCRAFT_CARRIER
        self.state = ClientState.WAITING_CONNECTION
        self.amountShips = {
            ShipType.AIRCRAFT_CARRIER: 1,
            ShipType.TANKER: 2,
            ShipType.DESTROYER: 3,
            ShipType.SUBMARINE: 4,
        }
        self.visualizeGrid = [None]
        self.playerGrid = [None]
        self.ships = []
        self.gridsFrame = Frame(self.root)
        self.gridsFrame.pack(side=TOP, expand=True)

    def __init__(self):
        self.serverSocket = None
        self.playerGrid = [None] #estrutura que guarda a matriz do tabuleiro do jogador
        self.visualizeGrid = [None] #estrutura que guarda a matriz para visualizaçao do navio a ser inserido
        self.isConnected = False #indica se o cliente realizou uma conexao com o servidor
        self.root = Tk()
        self.serverWin = True #indica se servidor ganhou
        self.playerWin = True #indica se jogador ganhou
        self.id = 0 #id de navio
        self.logLabelVar = StringVar()
        self.logLabelVar1 = StringVar()
        self.logLabelVar2 = StringVar()
        self.shipInitOrientation = IntVar()
        self.shipInitOrientation.set(Orientation.HORIZONTAL.value)
        self.shipInitType = ShipType.AIRCRAFT_CARRIER
        self.state = ClientState.WAITING_CONNECTION
        self.amountShips = { #quantidade de navio de cada tipo
            ShipType.AIRCRAFT_CARRIER: 1,
            ShipType.TANKER: 2,
            ShipType.DESTROYER: 3,
            ShipType.SUBMARINE: 4,
        }
        self.ships = []
        self.root.title("TP - Batalha Naval")
        self.root.geometry("800x500")
        self.playerFrame = None #frame para visualizaçao do tabuleiro do jogador
        self.serverFrame = None #frame para visualização do tabuleiro do servidor
        self.gridsFrame = None #frame para agrupar tabuleiros
        self.visualizePieceFrame = None #frame para visualizaçao de peça a ser inserida
        self.logLabelFrame = Frame(self.root)
        self.logLabelFrame.pack(side=BOTTOM, expand=True)
        self.logLabel = Label(self.logLabelFrame, textvariable=self.logLabelVar).pack(side=TOP, expand=True)
        self.logLabel1 = Label(self.logLabelFrame, textvariable=self.logLabelVar1).pack(side=TOP, expand=True)
        self.logLabel2 = Label(self.logLabelFrame, textvariable=self.logLabelVar2).pack(side=TOP, expand=True)
        # menu.add_command(label="Reiniciar", command=Restart, state=ENABLED if isConnected else DISABLED)
        # menu.add_command(label="Sair", command=Quit)


    def sendBoardToServer(self):
        boardString = ""
        for y in range (10):
            for x in range(10):
                cell = self.playerGrid[0][y][x]
                #se na posicao ha um navio, adiciona 1 a string de representação do tabuleiro
                if cell.ship:
                    boardString += "1"
                else: #caso contrario, adiciona 0
                    boardString += "0"
        print(boardString)
        self.serverSocket.sendall(str.encode(boardString)) #envia tabuleiro para o servidor
        self.initServerGrid() #inicializa representação do tabuleiro do servidor

    def changeVisualizePieceGrid(self):
        #se montando tabuleiro do jogador
        if self.state == ClientState.SETTING_PLAYER_SHIPS:
            yInc = 0
            xInc = 0
            size = self.shipInitType.value
            for x in range(0, 5):
                for y in range(0, 5):
                    self.visualizeGrid[0][y][x].button.configure(bg="white")
            #se orientação selecionada for horizontal, cresce para direita
            if self.shipInitOrientation.get() == Orientation.HORIZONTAL.value:
                xInc = 1
            else: #se orientação selecionada for vertical, cresce para baixo
                yInc = 1
            #atualiza cada célula na direção selecionada para a cor do tipo de navio
            for i in range(0, size):
                cell = self.visualizeGrid[0][0 + (yInc * i)][0 + (xInc * i)]
                cell.button.configure(bg=ShipTypeColor[self.shipInitType])
        else: #se terminou de montar tabuleiro, destrói matriz de visualização de peça
            self.visualizePieceFrame.destroy()


    def initVisualizePieceGrid(self):
        self.visualizePieceFrame = Frame(self.gridsFrame)
        self.visualizePieceFrame.pack(side=LEFT, expand=True)
        self.visualizeGrid = [None]
        visualizePieceGridFrame = None
        visualizePieceGridFrame = self.initGrid(self.visualizePieceFrame, visualizePieceGridFrame, self.visualizeGrid, Grid.VISUALIZE, lambda e: None, 5, 5, hasLabel=False)
        visualizePieceGridFrame.pack(side=TOP)
        #sempre que alterar orientação selecionada da peça, chama o método changeVisualizePieceGrid
        Radiobutton(self.visualizePieceFrame,
                    text="Vertical",
                    padx=20,
                    variable=self.shipInitOrientation,
                    command=self.changeVisualizePieceGrid,
                    value=Orientation.HORIZONTAL.value).pack(side=TOP)
        Radiobutton(self.visualizePieceFrame,
                    text="Horizontal",
                    padx=20,
                    variable=self.shipInitOrientation,
                    command=self.changeVisualizePieceGrid,
                    value=Orientation.VERTICAL.value).pack(side=TOP)
        self.changeVisualizePieceGrid()

    def initPlayerGrid(self):
        self.resetShipInitParams()
        self.state = ClientState.SETTING_PLAYER_SHIPS
        playerFrameContainer = Frame(self.gridsFrame)
        self.playerGrid = [None]
        self.playerFrame = self.initGrid(playerFrameContainer, self.playerFrame, self.playerGrid, Grid.PLAYER)
        self.playerFrame.pack(side=TOP, expand=True)
        Label(playerFrameContainer, text="Mapa do Jogador").pack(side=TOP, expand=True)
        self.initVisualizePieceGrid()
        playerFrameContainer.pack(side=LEFT, expand=True)

    def colorByMatrix(self, gridMatrix, xmax = 10, ymax = 10):
        for y in range(0, ymax):
            for x in range(0, xmax):
                if gridMatrix[0][y][x].ship:
                    gridMatrix[0][y][x].button.configure(bg=ShipTypeColor[self.shipInitType])

    def visualizeCheckHitAtPosition(self, gridMatrix, x, y):
        cell = gridMatrix[0][y][x] #pega célula na posição
        if(cell.checked): #se célula foi checada
            if(cell.hit): #se célula foi um acerto, atualiza botão para vermelho
                cell.button.configure(bg='red')
            else: #se célula foi um acerto, atualiza botão para mostrar um X
                cell.button.configure(text="X")
                cell.button.configure(font='sans 16 bold')
                #cell.button.configure(bg=rgbtohex(0, 27, 89))

    #parent -> a qual elemento o frame do tabuleiro estará dentro
    #gridFrame -> frame que irá conter o tabuleiro
    #gridMatrix -> matriz do tabuleiro
    #gridId -> tipo de matriz (Grid enum)
    #command -> qual comando é executado ao clicar em uma célula do tabuleiro
    #xmax -> número máximo de colunas
    #ymax -> número máximo de linhas
    #width -> largura das células
    #height -> altura das células
    #regenerateMatrix -> se deve reiniciar a matriz passada
    #hasLabel -> se deve mostrar as posições de cada eixo
    def initGrid(self, parent, gridFrame, gridMatrix, gridId, command = None, xmax = 10, ymax = 10, width = 30, height = 30, regenerateMatrix = True, hasLabel=True):
        if gridFrame: #se grid ja instanciado, o destroi
            gridFrame.destroy()
        gridFrame = Frame(parent, bg="black")
        if regenerateMatrix: #reinicia a matriz do tabuleiro
            gridMatrix[0] = [[None for x in range(xmax)] for y in range(ymax)]
        if hasLabel: #se tiver mostrando as posições dos eixos
            frame0 = Frame(gridFrame, width=width, height=height)
            frame0.propagate(False)
            frame0.grid(column=0, row=0, sticky="nsew")
            for y in range(0, ymax): #adiciona na esquerda do tabuleiro em cada linha
                frame = Frame(gridFrame, width=width, height=height)
                frame.propagate(False)
                Label(frame, text=str(y)).pack(side=TOP, expand=True, fill=BOTH)
                frame.grid(column=0, row=y+1, sticky="nsew")
            for x in range(0, xmax): #adiciona no topo do tabuleiro em cada coluna
                frame = Frame(gridFrame, width=width, height=height)
                frame.propagate(False)
                Label(frame, text=str(x)).pack(side=TOP, expand=True, fill=BOTH)
                frame.grid(column=x+1, row=0, sticky="nsew")
        for y in range(0, ymax):
            for x in range(0, xmax):
                frame = Frame(gridFrame, width=width, height=height)
                frame.propagate(False)
                frame.grid(column=y+1, row=x+1, sticky="nsew")
                button = Button(frame, bg=rgbtohex(0, 68, 227), command=command if command is not None else partial(self.cellAction, x, y, gridId)) #gera botão
                button.pack(expand=True, fill=BOTH)
                if regenerateMatrix:
                    gridMatrix[0][y][x] = (GridCell(x, y, button)) #gera nova célula e associa a posição da matriz
                else: #associa botão à célula da matriz
                    gridMatrix[0][y][x].button = button
        return gridFrame

    def setNextShipInitType(self):
        if self.shipInitType == ShipType.AIRCRAFT_CARRIER:
            self.shipInitType = ShipType.TANKER
        elif self.shipInitType == ShipType.TANKER:
            self.shipInitType = ShipType.DESTROYER
        elif self.shipInitType == ShipType.DESTROYER:
            self.shipInitType = ShipType.SUBMARINE
        else: #se ja inseriu todos os tipos
            self.state = ClientState.PLAYING
            self.sendBoardToServer() #envia tabuleiro montado pelo usuario para o servidor
        self.changeVisualizePieceGrid()

    def initServerGrid(self):
        serverFrameContainer = Frame(self.gridsFrame)
        self.serverGrid = [None]
        self.serverFrame = self.initGrid(serverFrameContainer, self.serverFrame, self.serverGrid, Grid.SERVER)
        self.serverFrame.pack(side=TOP, expand=True)
        Label(serverFrameContainer, text="Mapa do Servidor").pack(side=TOP, expand=True)
        serverFrameContainer.pack(side=LEFT, padx=(5, 0), expand=True)

    def requestCheckIfHit(self, x, y):
        requestStr = str(x) + "," + str(y)
        #envia posição clicada para o servidor
        self.serverSocket.sendall(str.encode(requestStr))
        #espera resposta do servidor
        data = self.serverSocket.recv(1024)
        print('Resposta: ', repr(data))
        #atualiza célula para indicar que posição foi checada
        self.serverGrid[0][y][x].checked = True
        #separa string retornada em variáveis
        serverBoardHit, serverLost, playerBoardHit, playerLost, xServer, yServer  = data.decode().split(',')
        winnerStr = ""
        #se jogador acertou um navio no tabuleiro do servidor
        if serverBoardHit == "True":
            #atualiza célula da representação do tabuleiro do servidor para indicar acerto
            self.serverGrid[0][y][x].hit = True
        #se servidor perdeu
        if serverLost == "True":
            #jogador ganhou
            self.playerWin = True
            #atualiza estado para indicar que o jogo acabou
            self.state = ClientState.END
            winnerStr = "Jogador ganhou!"
        #se jogador perdeu
        if playerLost == "True":
            #servidor ganhou
            self.serverWin = True
            #atualiza estado para indicar que o jogo acabou
            self.state = ClientState.END
            winnerStr = "Servidor ganhou!"
        #x e y que o servidor selecionou para atirar no tabuleiro do jogador
        serverX = int(xServer)
        serverY = int(yServer)
        #atualiza célula da representação do tabuleiro do jogador para indicar que posição foi checada
        self.playerGrid[0][serverY][serverX].checked = True
        #se servidor acertou um navio no tabuleiro do jogador
        if playerBoardHit == "True":
            #atualiza célula da representação do tabuleiro do servidor para indicar acerto
            self.playerGrid[0][serverY][serverX].hit = True
        playerStr = "Jogador: " + requestStr + " - " + ("Acertou!" if serverBoardHit == "True" else "Errou!")
        serverStr = "Servidor: " + xServer + "," + yServer + " - " + ("Acertou!" if playerBoardHit == "True" else "Errou!")
        self.logLabelVar.set(""+winnerStr)
        self.logLabelVar1.set(""+playerStr)
        self.logLabelVar2.set(""+serverStr)
        #atualiza célula do tabuleiro do servidor para mostrar acerto ou erro
        self.visualizeCheckHitAtPosition(self.serverGrid, x, y)
        #atualiza célula do tabuleiro do jogador para mostrar acerto ou erro
        self.visualizeCheckHitAtPosition(self.playerGrid, serverX, serverY)

    def cellAction(self, x, y, gridId):
        if self.state == ClientState.SETTING_PLAYER_SHIPS: #se usuario montando tabuleiro
            if gridId == Grid.PLAYER: #se clique em célula do tabuleiro do jogador
                if self.addShipToPosition(x, y): #se posicao valida
                    #subtrai 1 da quantidade disponivel do tipo atual de navio sendo inserido
                    self.amountShips[self.shipInitType] = self.amountShips[self.shipInitType] - 1
                    if self.amountShips[self.shipInitType] == 0: #se quantidade disponivel é igual a 0
                        self.setNextShipInitType() #passa para o proximo tipo para insercao
                else:
                    self.logLabelVar.set("Posição inválida")
        elif self.state == ClientState.PLAYING: #se cliente já está jogando
            if gridId == Grid.SERVER: #se a célula clicada for da representação do tabuleiro do servidor
               self.requestCheckIfHit(x, y) #envia para o servidor requisição para checar hit

    def addShipToPosition(self, x, y):
        if not self.playerGrid[0][y][x].ship: #se não tiver um navio já na posição
            xInc = 0
            yInc = 0
            size = self.shipInitType.value #tamanho do tipo de navio
            #se orientação horizontal, cresce pra direita
            if self.shipInitOrientation.get() == Orientation.HORIZONTAL.value:
                xInc = 1
            else: #se orientação vertical, cresce para baixo
                yInc = 1
            #se na posição clicada, ao tentar inserir o navio terá parte dele fora do limte do tabuleiro
            if y + ((size - 1) * yInc) > 9 or x + ((size - 1) * xInc) > 9:
                return False
            else: #posição dentro do limite
                #checa se as celulas que serão ocupados pelo navio já não estão ocupadas
                for i in range(0, size):
                    if self.playerGrid[0][y + (yInc * i)][x + (xInc * i)].ship:
                        return False

            ship = Ship(self.id) #cria novo navio
            #define orientação baseada na selecionada
            if self.shipInitOrientation.get() == Orientation.HORIZONTAL.value:
                ship.orientation = Orientation.HORIZONTAL
            else:
                Orientation.VERTICAL
            #define tipo do navio
            ship.type = self.shipInitType
            #adiciona navio a lista
            self.ships.append(ship)
            for i in range(0, size): #atualiza células ocupadas pelo navio
                cell = self.playerGrid[0][y + (yInc * i)][x + (xInc * i)]
                cell.ship = ship #célula referencia novo navio
                #botão da célula passa a mostrar a cor e tamanho do tipo de navio
                cell.button.configure(bg=ShipTypeColor[ship.type])
                cell.button.configure(text=ship.type.value)
                cell.button.configure(font='sans 16')
            self.id = self.id + 1
            return True
        return False

    def connect(self):
        self.serverSocket = socket.socket(socket.AF_INET, socket.SOCK_STREAM) #inicia socket
        ip, port = ConnectWindow().show() #abre modal
        try:
            if not ip:
                ip = "127.0.0.1"
            if not port:
                port = 7777
            else:
                port = int(port)
            self.serverSocket.connect((ip, port)) #conecta socket ao endereço especificado
            self.serverSocket.sendall(b'Conectando...')
            data = self.serverSocket.recv(1024) #fica esperando receber confirmacao de conexao
            print('Resposta: ', repr(data))
            self.isConnected = True
            self.logLabelVar.set("Conectado.")
            self.initPlayerGrid()
        except:
            self.logLabelVar.set("Erro de conexão!")
            self.isConnected = False
        self.changeMenuState()

    def show(self):
        # ---- Métodos menu -------
        self.menu = Menu(self.root)
        self.menu.add_command(label="Conectar", command=self.connect)
        self.root.config(menu=self.menu)
        self.root.mainloop()


Client().show()
