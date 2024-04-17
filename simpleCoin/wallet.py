"""This is going to be your wallet. Here you can do several things:
- Generate a new address (public and private key). You are going
to use this address (public key) to send or receive any transactions. You can
have as many addresses as you wish, but keep in mind that if you
lose its credential data, you will not be able to retrieve it.

- Send coins to another address
- Retrieve the entire blockchain and check your balance

If this is your first time using this script don't forget to generate
a new address and edit miner config file with it (only if you are
going to mine).

Timestamp in hashed message. When you send your transaction it will be received
by several nodes. If any node mine a block, your transaction will get added to the
blockchain but other nodes still will have it pending. If any node see that your
transaction with same timestamp was added, they should remove it from the
node_pending_transactions list to avoid it get processed more than 1 time.
"""
import sys
import requests
import base64
import json
import bls
import time

from petlib.bn import Bn
bls_params = bls.setup()
from bplib.bp import BpGroup, G2Elem, G1Elem
from miner_config import *

def wallet():
    response = None
    while response not in ["1", "2", "3", "4"]:
        response = input("""What do you want to do?
        1. Generate new wallet
        2. Send coins to another wallet
        3. Check transactions
        4. Quit\n""")
    if response == "1":
        generate_BLS_keys()
    elif response == "2":
        with open('public_key.pem', 'r') as file:
            lines = file.readlines()
            addr_from = lines[1].strip()
        with open('private_key.pem', 'r') as file:
            lines = file.readlines()
            private_key = lines[1].strip()
        addr_to = input("To: introduce destination wallet address\n")
        amount = input("Amount: number stating how much do you want to send\n")
        try:
            amount = int(amount)
        except ValueError:
            print("Amount needs to be an integer")
            quit()
        print("=========================================\n\n")
        print("Proceed?\n")
        response = input("y/n\n")
        if response.lower() == "n":
            return quit()  # return to main menu
        else:
            send_transaction(addr_from, private_key, addr_to, amount)
    elif response == "3":  # Will always occur when response == 3.
        check_transactions()
        return wallet()  # return to main menu
    else:
        quit()

def send_transaction(addr_from, private_key, addr_to, amount):
    timestamp = round(time.time())
    signature = sign_BLS_msg(private_key, amount, timestamp)
    url = config['MINER_NODE_URL'] + '/txion'
    payload = {"from": addr_from,
                "to": addr_to,
                "amount": amount,
                "signature": signature,
                "timestamp":timestamp}
    headers = {"Content-Type": "application/json"}

    res = requests.post(url, json=payload, headers=headers)
    print(res.text)

def check_transactions():
    """Retrieve the entire blockchain. With this you can check your
    wallets balance. If the blockchain is to long, it may take some time to load.
    """
    try:
        res = requests.get(config['MINER_NODE_URL'] + '/blocks')
        parsed = json.loads(res.text)
        print(json.dumps(parsed, indent=4, sort_keys=True))
    except requests.ConnectionError:
        print('Connection error. Make sure that you have run miner.py in another terminal.')

def generate_BLS_keys():
    global bls_params
    ([sk],[vk]) = bls.ttp_keygen(bls_params,1,1)
    # sk is Bn and vk is G1Elem
    private_key = base64.b64encode( bytes.fromhex(sk.hex())).decode()
    public_key = base64.b64encode(vk.export()).decode()

    
    with open("private_key.pem", "w") as f:
        f.write(F"Private Key:\n{private_key}")
    with open("public_key.pem", "w") as f:
        f.write(F"Public key:\n{public_key}")
    print(F"Keys saved to file.")

def sign_BLS_msg(private_key, amount, timestamp):
    global bls_params
    message = [str(amount) + str(timestamp)]
    sk = Bn.from_hex(base64.b16encode(base64.b64decode(private_key)).decode())
    sig = bls.sign(bls_params,sk,message)
    sig = base64.b64encode(sig.export()).decode()
    return sig


if __name__ == '__main__':
    config = configs[sys.argv[1]]
    print("""       =========================================\n
        OUR COIN v1.0.0 - BLOCKCHAIN SYSTEM\n
       =========================================\n\n
        You can find more help at: https://github.com/cosme12/SimpleCoin\n
        Make sure you are using the latest version or you may end in
        a parallel chain.\n\n\n""")
    wallet()
    input("Press ENTER to exit...")
