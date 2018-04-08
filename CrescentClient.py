import socket
import random


class CrescentClient(object):
    """A client for bidding with the AuctionRoom"""
    def __init__(self, host="localhost", port=8020, mybidderid=None, verbose=False, scaleUp=0.9, scaleDown=0.7):        
        # Default init info
        self.verbose = verbose
        self.roundBids = []
        self.aimedValue = 0
        self.scaleUp = scaleUp
        self.scaleDown = scaleDown
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.sock.connect((host,port))
        forbidden_chars = set(""" '".,;:{}[]()""")
        if mybidderid:
            if len(mybidderid) == 0 or any((c in forbidden_chars) for c in mybidderid):
                print("""mybidderid cannot contain spaces or any of the following: '".,;:{}[]()!""")
                raise ValueError
            self.mybidderid = mybidderid
        else:
            self.mybidderid = raw_input("Input team / player name : ").strip()  # this is the only thing that distinguishes the clients
            while len(self.mybidderid) == 0 or any((c in forbidden_chars) for c in self.mybidderid):
              self.mybidderid = raw_input("""You input an empty string or included a space  or one of these '".,;:{}[]() in your name which is not allowed (_ or / are all allowed)\n for example Emil_And_Nischal is okay\nInput team / player name: """).strip()
        self.sock.send(self.mybidderid.encode("utf-8"))

        data = self.sock.recv(5024).decode('utf_8')
        x = data.split(" ")
        if self.verbose:
            print("Have received response of %s" % ' '.join(x))
        if(x[0] != "Not" and len(data) != 0):
          self.numberbidders = int(x[0])
          if self.verbose:
              print("Number of bidders: %d" % self.numberbidders)
          self.numtypes = int(x[1])
          if self.verbose:
              print("Number of types: %d" % self.numtypes)
          self.numitems = int(x[2])
          if self.verbose:
              print("Items in auction: %d" % self.numitems)
          self.maxbudget = int(x[3])
          if self.verbose:
              print("Budget: %d" % self.maxbudget)
          self.neededtowin = int(x[4])
          if self.verbose:
              print("Needed to win: %d" % self.neededtowin)
          self.order_known = "True" == x[5]
          if self.verbose:
              print("Order known: %s" % self.order_known)
          self.auctionlist = []
          self.winnerpays = int(x[6])
          if self.verbose:
              print("Winner pays: %d" % self.winnerpays)
          self.values = {}
          self.artists = {}
          order_start = 7
          if self.neededtowin > 0:
              self.values = None
              for i in range(7, 7+(self.numtypes*2), 2):
                  self.artists[x[i]] = int(x[i+1])
                  order_start += 2
              if self.verbose:
                  print("Item types: %s" % str(self.artists))
          else:
              for i in range(7, 7+(self.numtypes*3), 3):
                  self.artists[x[i]] = int(x[i+1])
                  self.values[x[i]] = int(x[i+2])
                  order_start += 3
              if self.verbose:
                  print("Item types: %s" % str(self.artists))
                  print ("Values: %s" % str(self.values))

          if self.order_known:
              for i in range(order_start, order_start+self.numitems):
                  self.auctionlist.append(x[i])
              if self.verbose:
                  print("Auction order: %s" % str(self.auctionlist))

        self.sock.send('connected '.encode("utf-8"))

        data = self.sock.recv(5024).decode('utf_8')
        x = data.split(" ")
        if x[0] != 'players':
            print("Did not receive list of players!")
            raise IOError
        if len(x) != self.numberbidders + 2:
            print("Length of list of players received does not match numberbidders!")
            raise IOError
        if self.verbose:
         print("List of players: %s" % str(' '.join(x[1:])))

        self.players = []

        for player in range(1, self.numberbidders + 1):
          self.players.append(x[player])

        self.sock.send('ready '.encode("utf-8"))

        self.standings = {name: {artist : 0 for artist in self.artists} for name in self.players}
        for name in self.players:
          self.standings[name]["money"] = self.maxbudget

    def play_auction(self):
        winnerarray = []
        winneramount = []
        done = False
        while not done:
            data = self.sock.recv(5024).decode('utf_8')
            x = data.split(" ")
            if x[0] != "done":
                if x[0] == "selling":
                    currentitem = x[1]
                    if not self.order_known:
                        self.auctionlist.append(currentitem)
                    if self.verbose:
                        print("Item on sale is %s" % currentitem)
                    bid = self.determinebid(self.numberbidders, self.neededtowin, self.artists, self.values, len(winnerarray), self.auctionlist, winnerarray, winneramount, self.mybidderid, self.players, self.standings, self.winnerpays)
                    if self.verbose:
                        print("Bidding: %d" % bid)
                    self.sock.send(str(bid).encode("utf-8"))
                    data = self.sock.recv(5024).decode('utf_8')
                    x = data.split(" ")
                    if x[0] == "draw":
                        winnerarray.append(None)
                        winneramount.append(0)
                    if x[0] == "winner":
                        self.standings[x[1]][currentitem] += 1
                        self.standings[x[1]]["money"] -= int(x[3])
                        winnerarray.append(x[1])
                        winneramount.append(int(x[3]))
            else:
                done = True
                if self.verbose:
                    if self.mybidderid in x[1:-1]:
                        print("I won! Hooray!")
                    else:
                        print("Well, better luck next time...")
        self.sock.close()

    def determinebid(self, numberbidders, wincondition, artists, values, rd, itemsinauction, winnerarray, winneramount, mybidderid, players, standings, winnerpays):
        '''You have all the variables and lists you could need in the arguments of the function,
        these will always be updated and relevant, so all you have to do is use them.
        Write code to make your bot do a lot of smart stuff to beat all the other bots. Good luck,
        and may the games begin!'''

        '''
        numberbidders is an integer displaying the amount of people playing the auction game.

        wincondition is an integer. A postiive integer means that whoever gets that amount of a single type
        of item wins, whilst 0 means each itemtype will have a value and the winner will be whoever accumulates the
        highest total value before all items are auctioned or everyone runs out of funds.

        artists will be a dict of the different item types as keys with the total number of that type on auction as elements.

        values will be a dict of the item types as keys and the type value if wincondition == 0. Else value == None.

        rd is the current round in 0 based indexing.

        itemsinauction is a list where at index "rd" the item in that round is being sold is displayed. Note that it will either be as long as the sum of all the number of the items (as in "artists") in which case the full auction order is pre-announced and known, or len(itemsinauction) == rd+1, in which case it only holds the past and current items, the next item to be auctioned is unknown.

        winnerarray is a list where at index "rd" the winner of the item sold in that round is displayed.

        winneramount is a list where at index "rd" the amount of money paid for the item sold in that round is displayed.

        example: I will now construct a sentence that would be correct if you substituted the outputs of the lists:
        In round 5 winnerarray[4] bought itemsinauction[4] for winneramount[4] pounds/dollars/money unit.

        mybidderid is your name: if you want to reference yourself use that.

        players is a list containing all the names of the current players.

        standings is a set of nested dictionaries (standings is a dictionary that for each person has another dictionary
        associated with them). standings[name][artist] will return how many paintings "artist" the player "name" currently has.
        standings[name]['money'] (remember quotes for string, important!) returns how much money the player "name" has left.

            standings[mybidderid] is the information about you.
            I.e., standings[mybidderid]['money'] is the budget you have left.

        winnerpays is an integer representing which bid the highest bidder pays. If 0, the highest bidder pays their own bid,
        but if 1, the highest bidder instead pays the second highest bid (and if 2 the third highest, ect....). Note though that if you win, you always pay at least 1 (even if the second-highest was 0).

        Don't change any of these values, or you might confuse your bot! Just use them to determine your bid.
        You can also access any of the object variables defined in the constructor (though again don't change these!), or declare your own to save state between determinebid calls if you so wish.

        determinebid should return your bid as an integer. Note that if it exceeds your current budget (standings[mybidderid]['money']), the auction server will simply set it to your current budget.

        Good luck!
        '''

        # Game 1: First to buy wincondition of any artist wins, highest bidder pays own bid, auction order known.
        if (wincondition > 0) and (winnerpays == 0) and self.order_known:
            return self.first_bidding_strategy(numberbidders, wincondition, artists, values, rd, itemsinauction, winnerarray, winneramount, mybidderid, players, standings, winnerpays)

        # Game 2: First to buy wincondition of any artist wins, highest bidder pays own bid, auction order not known.
        if (wincondition > 0) and (winnerpays == 0) and not self.order_known:
            return self.second_bidding_strategy(numberbidders, wincondition, artists, values, rd, itemsinauction, winnerarray, winneramount, mybidderid, players, standings, winnerpays)

        # Game 3: Highest total value wins, highest bidder pays own bid, auction order known.
        if (wincondition == 0) and (winnerpays == 0) and self.order_known:
            return self.third_bidding_strategy(numberbidders, wincondition, artists, values, rd, itemsinauction, winnerarray, winneramount, mybidderid, players, standings, winnerpays)

        # Game 4: Highest total value wins, highest bidder pays second highest bid, auction order known.
        if (wincondition == 0) and (winnerpays == 1) and self.order_known:
            return self.fourth_bidding_strategy(numberbidders, wincondition, artists, values, rd, itemsinauction, winnerarray, winneramount, mybidderid, players, standings, winnerpays)

        # Though you will only be assessed on these four cases, feel free to try your hand at others!
        # Otherwise, this just returns a random bid.
        return self.random_bid(standings[mybidderid]['money'])

    def random_bid(self, budget):
        """Returns a random bid between 1 and left over budget."""
        return int(budget*random.random()+1)

    def first_bidding_strategy(self, numberbidders, wincondition, artists, values, rd, itemsinauction, winnerarray, winneramount, mybidderid, players, standings, winnerpays):
        """Game 1: First to buy wincondition of any artist wins, highest bidder pays own bid, auction order known."""
        
        artistValuation = {}
        
        for artist in artists:
            artistValuation[artist] = 0
        
        curr_item = itemsinauction[rd]
        
        # TODO need to factor in previous buys from other bidders
        # Know the order of auctioned items, so we can bid on the ones we think are most likely to win for us early
        for roundItem in itemsinauction[rd:]:
            artistValuation[roundItem] += 1
            # TODO Could find a way to factor in number of bidders 
            if artistValuation[roundItem] - standings[mybidderid][roundItem] >= wincondition:
                # This means we want to follow the path to this item type and ignore others
                if curr_item != roundItem:
                    return 0
                # If we own 2 of this item already, we want to go all in
                if standings[mybidderid][curr_item] == 2:
                    return standings[mybidderid]['money']
                # If we own 1 of these already, let's try spending half our money on it!
                if standings[mybidderid][curr_item] == 1:
                    return int(standings[mybidderid]['money']/2)
                else:
                    return int(standings[mybidderid]['money']/3)
        

    def second_bidding_strategy(self, numberbidders, wincondition, artists, values, rd, itemsinauction, winnerarray, winneramount, mybidderid, players, standings, winnerpays):
        """Game 2: First to buy wincondition of any artist wins, highest bidder pays own bid, auction order not known."""
        
        # Don't have access to the order, so need to estimate for the ordering using previous items
        # Also have access to total for the types in artists
        
        artistValuation = {}
        
        for artist in artists:
            artistValuation[artist] = artists[artist]
            
        for roundItem in itemsinauction[:rd]:
            artistValuation[roundItem] -= 1
        
        # Really, we want to value ones we've already got some of much higher!
        for ownedItem in standings[mybidderid]:
            if ownedItem != 'money':
                artistValuation[ownedItem] *= (standings[mybidderid][ownedItem]+1)
                
        curr_item = itemsinauction[rd]
        
        # Make sure we are making the best choice
        bestChoice = [curr_item, artistValuation[curr_item]]
        for artist in artistValuation:
            if artistValuation[artist] > bestChoice[1]:
                bestChoice[0] = artist
                bestChoice[1] = artistValuation[artist]
                
        # Now actually make the bid
        if bestChoice[0] != curr_item:
            return 0
        else:
            # If we own 2 of this item already, we want to go all in
            if standings[mybidderid][curr_item] == 2:
                return standings[mybidderid]['money']
            # If we own 1 of these already, let's try spending half our money on it!
            if standings[mybidderid][curr_item] == 1:
                return int(standings[mybidderid]['money']/2)
            else:
                return int(standings[mybidderid]['money']/3)

    def third_bidding_strategy(self, numberbidders, wincondition, artists, values, rd, itemsinauction, winnerarray, winneramount, mybidderid, players, standings, winnerpays):
        """Game 3: Highest total value wins, highest bidder pays own bid, auction order known."""
        
        # Exit early if we have no budget
        if standings[mybidderid]['money'] == 0: return 0
        
        # TODO the real aim here is decide on the optimal set of items which will earn a majority?
        # Is it good enough to get maxValue/numberbidders? Not if there are non-rational auctioneers
        # Can also be a problem with cooperative clients against this bot
        
        # TODO need to decide the set of items we want to buy
        # Need to minimise the amount of items we need to buy, to minimise chance of losing
        # Want to take the largest items, as priority, then the smaller items in descending order
        
        # Need to sum the total valuation for an accurate representation of what the majority is
        totalValue = 0
        for item in itemsinauction:
            totalValue += values[item]
        
        
        # Make sure to keep track of what the maximum and minimum value bounds we shouldn't pass over
        upperValueCap = int(totalValue/2)+1
        lowerValueCap = int(totalValue/len(players))+1
        # Looking for the majority of valuated points
        if self.aimedValue == 0:
            self.aimedValue = upperValueCap
        aimedValue = self.aimedValue
        
        # If this isn't the first round, scale the aimedValue dependent on previous rounds success
        if rd != 0 and self.roundBids[rd-1] != 0:
            if winnerarray[rd-1] == mybidderid:
                aimedValue /= self.scaleUp
                if aimedValue > upperValueCap:
                    aimedValue = upperValueCap
            else:
                aimedValue *= self.scaleDown
                if aimedValue < lowerValueCap:
                    aimedValue = lowerValueCap
        
        # Need to scale the valuation based on previous round successes
        # We don't have previously bidded values, so we can only look at who won
        # And estimate what we bidded at the time
        currentBudget = self.maxbudget
        remainingValue = totalValue
        targetItems = {}
        itemsInValuedOrder = []
        currentVal = 0
        for artist in artists:
            targetItems[artist] = 0
            currentVal += standings[mybidderid][artist]*values[artist]
            
        # Loop over and order items in descending value order with an insertion sort
        for artist in artists:
            nextPlace = False
            for art in artists:
                if ((nextPlace == False 
                or values[nextPlace] < values[art])
                and not (art in itemsInValuedOrder)):
                    nextPlace = art
            itemsInValuedOrder.append(nextPlace)
        
        #if rd == 0:
            #print(itemsInValuedOrder)
        
        # If we are already at the aimed value, see if we can't get a little bit more item wise
        if currentVal >= aimedValue:
            aimedValue /= self.scaleUp
            if aimedValue > upperValueCap:
                aimedValue = upperValueCap
        
        # Step through future rounds looking for highest value items first
        targetVal = aimedValue
        for index, artist in enumerate(itemsInValuedOrder):
            for item in itemsinauction[rd:]:
                # Break if we have reached the target value
                if targetVal < currentVal:
                    break
                elif artist == item:
                    targetItems[artist] += 1
                    targetVal -= values[artist]
            
        itemWorth = 0
        # Only bid if this item is in our bid set
        if targetItems[itemsinauction[rd]] > 0:
            itemWorth = int((values[item]/(aimedValue-currentVal))*currentBudget)
            
        
        self.roundBids.append(itemWorth)
        self.aimedValue = aimedValue
        return itemWorth + 1
        
    def fourth_bidding_strategy(self, numberbidders, wincondition, artists, values, rd, itemsinauction, winnerarray, winneramount, mybidderid, players, standings, winnerpays):
        """Game 4: Highest total value wins, highest bidder pays second highest bid, auction order known."""

        # Already shown that bidding the personal valuation is a dominant strategy
        return self.third_bidding_strategy(numberbidders, wincondition, artists, values, rd, itemsinauction, winnerarray, winneramount, mybidderid, players, standings, winnerpays)