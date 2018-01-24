import gdax
import time
import os
import ccxt
import private

def Buy(curpair, price, size):
	try:
		auth_client.buy(price=price, size=size, product_id=curpair)
	except Exception as e:
		return e

def Trailing(curpair, price, size, goal, originalPrice, stopLoss):
	try:
		binance = ccxt.binance()
		binance.apiKey = private.binanceKey
		binance.secret = private.binanceSecret
		currentPrice = float(ccxt.binance().fetch_ticker(curpair)['last'])
		price = "{:.7f}".format(float(price))
		#buyPair = auth_client.buy(size=size, product_id=curpair, type="market")
		#time.sleep(5)
		stopLossSell = binance.createLimitSellOrder(curpair, size, stopLoss, { 'type': 'stop_loss_limit', 'stopPrice': "{:7f}".format(float(stopLoss)) })
		#StoreOrder(str(stopLossSell["id"]), curpair, price, size, goal, originalPrice, stopLoss)
		print("Order: " + str(stopLossSell["id"]))
		print("Setting stop loss: " + str(stopLossSell["price"]))
		print("Will start trailing at, " + str(price) + ", with TP at, " + str(GetPercentage(curpair, goal - 1, priceToUse=originalPrice)))
		time.sleep(5)
		while (stopLossSell["status"] != "closed"):
			currentPrice = float(ccxt.binance().fetch_ticker(curpair)['last'])
			doot = "Bought: {0:9} Current: {1:9} Stop: {2:9} Take: {3:9} Goal(%): {4:9}".format(str(originalPrice), str(currentPrice), str(stopLossSell["price"]), str(price), str(goal))
			print(doot)
			if ("{:.7f}".format(float(currentPrice)) > "{:.7f}".format(float(price))):
				trailingPrice = GetPercentage(curpair, goal - 1, priceToUse=originalPrice)
				print("Setting take profit: " + str(trailingPrice))
				#DeleteOrder(str(stopLossSell["id"]))
				binance.cancel_order(str(stopLossSell["id"]), curpair)
				try:
					profitSell = binance.createLimitSellOrder(curpair, size, trailingPrice, { 'type': 'stop_loss_limit', 'stopPrice': "{:7f}".format(float(trailingPrice)) })
				except:
					continue
				#StoreOrder(str(profitSell["id"]), curpair, price, size, goal, originalPrice, stopLoss)
				while(profitSell["status"] != "closed"):
					print("Bought: " + str(originalPrice) + ", Current: " + str(currentPrice) + ", Stop: " + str(trailingPrice) + ", Increase: " + str(GetPercentage(curpair, goal + 1, priceToUse=originalPrice)) + ", Goal(%): " + str(goal))
					if ("{:.7f}".format(float(currentPrice)) >= GetPercentage(curpair, goal + 1, priceToUse=originalPrice)):
						goal += 1
						binance.cancel_order(str(profitSell["id"]), curpair)
						trailingPrice = GetPercentage(curpair, goal - 1, priceToUse=originalPrice)
						try:
							profitSell = binance.createLimitSellOrder(curpair, size, trailingPrice, { 'type': 'stop_loss_limit', 'stopPrice': "{:7f}".format(float(trailingPrice)) })
						except:
							continue
					time.sleep(45)
					currentPrice = float(ccxt.binance().fetch_ticker(curpair)['last'])
					if ("{:.7f}".format(float(currentPrice)) < "{:.7f}".format(float(trailingPrice))):
						#DeleteOrder(str(profitSell["id"]))
						return("Posistion closed.")
			time.sleep(45)
	except Exception as e:
		print(e)

def StoreOrder(orderID, curpair, price, size, goal, originalPrice, stopLoss):
	with open(orderID + ".txt") as file:
		file.write(str("{}, {}, {}, {}, {}, {}").format(curpair, price, size, goal, originalPrice, stopLoss))

def DeleteOrder(orderID):
	os.remove(str(orderID))

def GetPercentage(curpair, goal, stopLoss=False, priceToUse=0):
	try:
		curpair = int(curpair)
		if priceToUse == 0:
			if stopLoss == True:
				pairPrice = curpair
				goalPrice = pairPrice - (pairPrice * (goal / 100))
			else:
				pairPrice = curpair
				goalPrice = pairPrice + (pairPrice * (goal / 100))
		elif priceToUse != 0:
			if stopLoss == True:
				goalPrice = priceToUse - (priceToUse * (goal / 100))
			else:
				goalPrice = priceToUse + (priceToUse * (goal / 100))
		return float(goalPrice)
	except:
		if priceToUse == 0:
			if stopLoss == True:
				pairPrice = float(ccxt.binance().fetch_ticker(curpair)['last'])
				goalPrice = pairPrice - (pairPrice * (goal / 100))
			else:
				pairPrice = float(ccxt.binance().fetch_ticker(curpair)['last'])
				goalPrice = pairPrice + (pairPrice * (goal / 100))
		elif priceToUse != 0:
			if stopLoss == True:
				goalPrice = priceToUse - (priceToUse * (goal / 100))
			else:
				goalPrice = priceToUse + (priceToUse * (goal / 100))
		return "{:.7f}".format(float(goalPrice))

def Menu():
	print("\n\n(1) - Buy")
	print("(2) - Get Stop Price")
	print("(3) - Set Trailing")
	selection = input("Selection: ")

	if (selection == "1"):
		curpair = input("Pair: ")
		price = input("Price: ")
		size = input("Size: ")
		print(Buy(curpair, price, size))
	if (selection == "2"):
		curpair = input("Pair or Price: ")
		goal = int(input("Goal (%): "))
		print(GetPercentage(curpair, goal))
	if (selection == "3"):
		curpair = input("Pair: ")
		goal = int(input("Profit goal (%): "))
		stopLoss = int(input("Stop loss (%): "))
		price = float(GetPercentage(curpair, goal))
		size = float(input("Size: "))
		originalPrice = float(input("Entry Price: "))
		stopLoss = GetPercentage(curpair, stopLoss, stopLoss=True)
		print(Trailing(curpair, price, size, goal, originalPrice, float(stopLoss)))


if __name__ == "__main__":
	while (True):
		Menu()