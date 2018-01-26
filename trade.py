import gdax
import time
import os
import ccxt
import private
from datetime import datetime
import csv
from tinydb import TinyDB, Query

def Buy(curpair, price, size):
	try:
		auth_client.buy(price=price, size=size, product_id=curpair)
	except Exception as e:
		return e

# This function does the monititoring of prices & setting/resetting trades
def Trailing(curpair, price, size, goal, originalPrice, stopLoss):
	try:
		binance = ccxt.binance()
		binance.apiKey = private.binanceKey
		binance.secret = private.binanceSecret

		currentPrice = float(ccxt.binance().fetch_ticker(curpair)['last'])
		# Price is the price we want to achieve before starting to trail
		price = "{:.7f}".format(float(price))
		# This is the first order. Our lowest limit that we'll allow the price to hit before cutting our losses
		stopLossSell = binance.createLimitSellOrder(curpair, size, stopLoss, { 'type': 'stop_loss_limit', 'stopPrice': "{:7f}".format(float(stopLoss)) })
		StoreOrder(str(stopLossSell["id"]), curpair, price, size, goal, originalPrice, stopLoss)
		print("Order: " + str(stopLossSell["id"]))
		print("Setting stop loss: " + str(stopLossSell["price"]))
		print("Will start trailing at, " + str(price) + ", with TP at, " + str(GetPercentage(goal - 1, originalPrice)))
		time.sleep(5)
		while (stopLossSell["status"] != "closed"):
			currentPrice = float(ccxt.binance().fetch_ticker(curpair)['last'])
			pairInfo = "Time: {:9} Bought: {:9} Current: {:9} Stop: {:9} Take: {:9} Goal(%): {:9}".format(str(datetime.now().time().strftime("%H:%M:%S")), str(originalPrice), str(currentPrice), str(stopLossSell["price"]), str(price), str(goal))
			print(pairInfo)
			# If we've reached the point where we want to start a trail
			if ("{:.7f}".format(float(currentPrice)) > "{:.7f}".format(float(price))):
				# We're going to set our trailing price 1% lower than our take price (if we want to take at 5% we'll set our trail at 4%)
				trailingPrice = GetPercentage(goal - 1, originalPrice)
				print("Setting take profit: " + str(trailingPrice))
				DeleteOrder(str(stopLossSell["id"]))
				binance.cancel_order(str(stopLossSell["id"]), curpair)
				try:
					profitSell = binance.createLimitSellOrder(curpair, size, trailingPrice, { 'type': 'stop_loss_limit', 'stopPrice': "{:7f}".format(float(trailingPrice)) })
				except:
					continue
				StoreOrder(str(profitSell["id"]), curpair, price, size, goal, originalPrice, stopLoss)
				while(profitSell["status"] != "closed"):
					print("Bought: " + str(originalPrice) + ", Current: " + str(currentPrice) + ", Stop: " + str(trailingPrice) + ", Increase: " + str(GetPercentage(curpair, goal + 1, priceToUse=originalPrice)) + ", Goal(%): " + str(goal))
					if ("{:.7f}".format(float(currentPrice)) >= GetPercentage(goal + 1, originalPrice)):
						goal += 1
						binance.cancel_order(str(profitSell["id"]), curpair)
						trailingPrice = GetPercentage(goal - 1, originalPrice)
						try:
							profitSell = binance.createLimitSellOrder(curpair, size, trailingPrice, { 'type': 'stop_loss_limit', 'stopPrice': "{:7f}".format(float(trailingPrice)) })
						except:
							continue
					time.sleep(45)
					currentPrice = float(ccxt.binance().fetch_ticker(curpair)['last'])
					if ("{:.7f}".format(float(currentPrice)) < "{:.7f}".format(float(trailingPrice))):
						DeleteOrder(str(profitSell["id"]))
						return("Posistion closed.")
			time.sleep(45)
	except Exception as e:
		print(e)

def StoreOrder(orderID, curpair, price, size, goal, originalPrice, stopLoss):
	db = TinyDB("activetrades.json")
	db.insert({"ID": str(orderID), "Pair": str(curpair), "Take": str(price), "Goal": str(goal), "Stop": str(stopLoss), "Size": str(size), "Entry": str(originalPrice)})
		
def DeleteOrder(orderID):
	db = TinyDB("activetrades.json")
	order = Query()
	db.remove(order.ID == str(orderID))
	db.all()

def ListActiveOrders():
	db = TinyDB("activetrades.json")
	for item in db:
		print(item)

def RestartOrder(orderID):
	db = TinyDB("activetrades.json")
	binance = ccxt.binance()
	binance.apiKey = private.binanceKey	
	binance.secret = private.binanceSecret

	order = Query()
	curpair = db.search(order.ID == str(orderID))[0]["Pair"]
	price = float(db.search(order.ID == str(orderID))[0]["Take"])
	size = float(db.search(order.ID == str(orderID))[0]["Size"])
	goal = int(db.search(order.ID == str(orderID))[0]["Goal"])
	originalPrice = float(db.search(order.ID == str(orderID))[0]["Entry"])
	stopLoss = float(db.search(order.ID == str(orderID))[0]["Stop"])
	
	binance.cancel_order(str(orderID), curpair)
	DeleteOrder(orderID)
	print(Trailing(curpair, price, size, goal, originalPrice, float(stopLoss)))

def GetPercentage(goal, priceToUse, stopLoss=False):
	try:
		priceToUse = float(priceToUse)
		# Are we calculating our profit, or our stop loss
		if stopLoss == False:
			goalPrice = priceToUse + (priceToUse * (goal / 100))
		elif stopLoss == True:
			goalPrice = priceToUse - (priceToUse * (goal / 100))
		return float(goalPrice)
	except Exception as e:
		return str(e)


def Menu():
	print("\n\n(1) - Buy")
	print("(2) - Get Stop Price")
	print("(3) - Set Trailing")
	print("(4) - Restart Tracked Order")
	print("(5) - Delete Tracked Order")
	selection = input("Selection: ")

	if (selection == "1"):
		curpair = input("Pair: ")
		price = input("Price: ")
		size = input("Size: ")
		print(Buy(curpair, price, size))
	if (selection == "2"):
		originalPrice = float(input("Price: "))
		goal = int(input("Goal (%): "))
		print(GetPercentage(goal, originalPrice))
	if (selection == "3"):
		curpair = input("Pair: ")
		goal = int(input("Profit goal (%): "))
		stopLoss = int(input("Stop loss (%): "))
		size = float(input("Size: "))
		originalPrice = float(input("Entry Price: "))
		price = float(GetPercentage(goal, originalPrice))
		stopLoss = GetPercentage(stopLoss, originalPrice, stopLoss=True)
		print(Trailing(curpair, price, size, goal, originalPrice, float(stopLoss)))
	if (selection == "4"):
		ListActiveOrders()
		orderID = input("\nOrder ID: ")
		RestartOrder(orderID)
	if (selection == "5"):
		orderID = input("Order ID: ")
		DeleteOrder(orderID)



if __name__ == "__main__":
	while (True):
		Menu()