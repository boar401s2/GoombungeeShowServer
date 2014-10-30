from webconnserver import WebSocketServer
from eventhandler import EventHandler
from events import *
import logging, time, datetime, code
from config import *
from queuemanager import QueueManager
import BaralabaBob

class Application:
    def __init__(self):
        pass

    """ Starts the ball rolling """
    def start(self):
        self.initLogging()

        self.hexapod = BaralabaBob.Hexapod(("localhost", 1997))
        self.hexapod.start()

        self.queuemanager = QueueManager()

        self.webSocketServer = WebSocketServer()
        self.webSocketServer.start()

        EventHandler.addListener("echo", Events.PACKET_RECEIVED, self.onPacketReceived)

        self.loop()

    """ Sets up the logging """
    def initLogging(self):
        self.logger = logging.getLogger(Config.LOGGING_NAME)
        self.logger.setLevel(logging.DEBUG)

        ts = time.time()
        #TODO: Uncomment for long term logging, not testing
        st = datetime.datetime.fromtimestamp(ts).strftime('%Y-%m-%d')# %H.%M.%S')
        fh = logging.FileHandler("logs/%s.txt"%st)
        fh.setLevel(logging.DEBUG)

        ch = logging.StreamHandler()
        ch.setLevel(logging.INFO)

        formatter = logging.Formatter("%(created)f %(thread)d %(filename)s,%(lineno)d %(levelname)s: %(message)s")
        fh.setFormatter(formatter)
        ch.setFormatter(formatter)

        self.logger.addHandler(fh)
        self.logger.addHandler(ch)

    """ The main loop of the program"""
    def loop(self):
        code.interact(local=locals())
        pass

    def onPacketReceived(self, data):
        packet = data[0]
        sendFunc = data[1]
        def respond(value):
            sendFunc(('{"%s":"%s"}\n' % ("response", value)).encode("UTF-8"))

        if "command" in packet:
            args = packet["command"].split(" ")

            if args[0] == "ping":
                respond("pong")
            elif args[0] == "handshake":
                gen = self.queuemanager.generateID()
                respond("handshook %s"%gen)
                self.logger.info("New connection. ID assigned %s" % gen)
            elif args[0] == "cookieDump":
                self.logger.debug("Cookie dump: %s"%args[1])
                respond("ok")
            elif args[0] == "queue":
                result = self.queuemanager.addToQueue(args[1])
                if result:
                    respond("queued")
                else:
                    respond("error")
            elif args[0] == "getControlTime":
                respond(str(Config.CONTROL_TIME))
            elif args[0] == "getQueuedPeople":
                respond(self.queuemanager.getPlaceInQueue(args[1]))
            elif args[0] == "getETA":
                respond(self.queuemanager.getTimeUntilTurn(args[1]))
            elif args[0] == "isTurn":
                respond(self.queuemanager.isTurn(args[1]))


            elif args[0] == "robot":
                self.handleRobotCommand(args, sendFunc)


            else:
                respond("UNKNOWN COMMAND")

        else:
            respond("Command not found")

    #command id command
    def handleRobotCommand(self, args, sendFunc):
        #Bunch of messy util stuff...
        del args[0];
        def respond(value):
            sendFunc(('{"%s":"%s"}\n' % ("response", value)).encode("UTF-8"))
        if not self.queuemanager.isTurn(args[0]):
            respond("turnDone")
            return
        else:
            respond("ok")
        #Fun stuff!
        command = args[1]

        if command == "closeJaw":
            self.hexapod.legs.turnOn()
        elif command == "openJaw":
            self.hexapod.legs.turnOff();

    def shutdown(self):
        EventHandler.callEvent(Events.SERVER_SHUTDOWN, None)
        exit()




if __name__ == "__main__":
    app = Application()
    app.start()
else:
    print("This project is not a library! It has to be run as a standalone program.")