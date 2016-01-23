#!/usr/bin/env python2

import requests
import json
import time
import sys
import argparse


class Xmr():

    def __init__(self, tor=False):
        self.headers = {"Content-Type": "application/json"}
        self.xmrapi = "https://xmr.to/api/v1/xmr2btc/"
        self.walletapi = "http://localhost:18082/json_rpc"
        self.tor = tor

    def usdtobtc(self, amount):
        tick = requests.get("https://poloniex.com/public?command=returnTicker")
        divideby = float(tick.json()["USDT_BTC"]["last"])
        btc = round(float(amount) / divideby, 8)
        return str(btc)

    def gentrans(self, amount, destination, usd):
        if usd:
            amount = self.usdtobtc(amount)
        params = {"btc_amount": amount, "btc_dest_address": destination}
        api = self.xmrapi + "order_create/"
        _r = self.post(params, api, local=False)
        return _r.json()["uuid"]

    def getstatus(self, uuid):
        params = {"uuid": uuid}
        api = self.xmrapi + "order_status_query/"
        _r = self.post(params, api, local=False)
        return _r.json()

    def post(self, params, api, local=True):
        if not local and self.tor:
            print "using tor to connect to %s" % api
            proxies = {"http": "socks5://localhost:9050",
                       "https": "socks5://localhost:9050"}
        _r = requests.post(api,
                           headers=self.headers,
                           data=json.dumps(params))
        return _r

    def sendxmr(self, _r):
        amount = self.toxmrvalue(_r["xmr_required_amount"])
        dest = [{'address': _r["xmr_receiving_address"],
                'amount': amount}]
        params = {"method": "transfer",
                  "params": {"destinations": dest,
                             "payment_id": _r["xmr_required_payment_id"],
                             "fee": 0,
                             "mixin": 3,
                             "unlock_time": 0}}
        params.update({"id": 0, "jsonrpc": "2.0"})

        self.post(params, self.walletapi)

    def toxmrvalue(self, amount):
        amount = str(amount)
        padding = 12
        leadpadding = 0
        if amount.count("."):
            first, last = amount.split(".")
            first = first.lstrip("0")
            last = last.rstrip("0")
            amount = first + last
            padding = padding - len(last)
            if first == "":
                leadpadding += 1
        rr = "0"*leadpadding + amount + "0"*padding
        return int(rr)

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Send btc via xmr.to")
    parser.add_argument("amount")
    parser.add_argument("address")
    parser.add_argument("-u", "--usd", action='store_true')
    parser.add_argument("-t", "--tor", action='store_true')
    args = parser.parse_args()
    amount = args.amount
    destination = args.address
    usd = args.usd
    tor = args.tor

    _t = Xmr(tor=tor)
    uuid = _t.gentrans(amount, destination, usd)
    _r = _t.getstatus(uuid)
    while _r["state"] == "TO_BE_CREATED":
        print("Waiting for transaction to be created")
        time.sleep(2)
        _r = _t.getstatus(uuid)
    _t.sendxmr(_r)
    _r = _t.getstatus(uuid)
    while _r["state"] != "BTC_SENT":
        print("Waiting for transaction to be paid")
        time.sleep(15)
        _r = _t.getstatus(uuid)
    else:
        print("Transaction sent!")
