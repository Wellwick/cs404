from multiprocessing import Process
from AuctionClient import AuctionClient
from AuctionServer import AuctionServer
from BulwarkClient import BulwarkClient
from CrescentClient import CrescentClient
import time

HOST = "localhost"
ports = 8060
numbidders = 25
numtest = 25
neededtowin = 0
itemtypes = ['Picasso', 'Van_Gogh', 'Rembrandt', 'Da_Vinci']
#numitems = {'Picasso': 50, 'Van_Gogh' : 40, 'Rembrandt' : 30, 'Da_Vinci' : 10}
numitems = {}
auction_size = 200
budget = 1000
values = {'Picasso': 1, 'Van_Gogh' : 5, 'Rembrandt' : 10, 'Da_Vinci' : 20}
announce_order = True
winner_pays = 0

args = (HOST, ports, numbidders, neededtowin, itemtypes, numitems, auction_size, budget, values, announce_order, winner_pays
, )

verbose = False


def run_auction(host, ports, numbidders, neededtowin, itemtypes, numitems, auction_size, budget, values, announce_order, winner_pays):
    auctionroom = AuctionServer(host=host, ports=ports, numbidders=numbidders, neededtowin=neededtowin,
    itemtypes=itemtypes, numitems=numitems, auction_size=auction_size, budget=budget, values=values, announce_order=announce_order, winner_pays=winner_pays)
    auctionroom.announce_auction()
    auctionroom.run_auction()


def run_client(port, bidderid, verbose, scaleUp, scaleDown):
    bidbot = CrescentClient(port=port, mybidderid=bidderid, verbose=verbose, scaleUp=scaleUp, scaleDown=scaleDown)
    bidbot.play_auction()


if __name__=='__main__':
     #print("Starting AuctionServer")
     auctionserver = Process(target = run_auction, args = args)
     auctionserver.start()
     time.sleep(2)
     bidbots = []
     for i in range(numbidders):
         p = ports + i
         index = int((i - (i % 5))/5)
         scaleUp = 70 + ((i % 5)* 5)
         scaleDown = 70 + (index * 5)
         name = "CrescentDown" + str(int(scaleDown)) + "Up" + str(int(scaleUp))
         #print("Starting AuctionClient on port %d with name %s" % (p, name))
         b = Process(target = run_client, args = (p, name, verbose, scaleUp/100, scaleDown/100))
         bidbots.append(b)
         b.start()
         time.sleep(1)