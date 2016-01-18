#!/usr/bin/env python2

import requests
import json
import time
import sys

class Xmr():
    def __init__(self):
        self.headers = {"Content-Type": "application/json"}
        self.xmrapi = "https://xmr.to/api/v1/xmr2btc/"
        self.walletapi = "http://localhost:18082/json_rpc"

    def gentrans(self, amount, destination):
        params = {"btc_amount": amount, "btc_dest_address": destination}
        api = self.xmrapi + "order_create/"
        _r = self.post(params, api)
        return _r.json()["uuid"]

    def getstatus(self, uuid):
        params = {"uuid": uuid}
        api = self.xmrapi + "order_status_query/"
        _r = self.post(params, api)
        return _r.json()

    def post(self, params, api):
        _r = requests.post(api, headers=self.headers,
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
                      "unlock_time": 0}
                 }
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
    if len(sys.argv) != 3:
        print "%s [amount in btc] [destination address]" % sys.argv[0]
        sys.exit(1)
    amount = sys.argv[1]
    destination = sys.argv[2]
    _t = Xmr()
    uuid = _t.gentrans(amount, destination)
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
