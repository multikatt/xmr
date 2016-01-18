# xmr
Automatically send btc via xmr.to!

# usage
This script needs simplewallet running and listening on rpc port 18082. For example ```simplewallet --rpc-bind-port=18082 --password "passwd" --wallet-file wallet```

then
```
pip install -r requirements
./xmr.py [amount in btc] [destination address]
```

Use this script on your own risk, it's very untested!
