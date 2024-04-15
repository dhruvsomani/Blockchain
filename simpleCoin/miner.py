import sys
import ast
import time
import hashlib
import json
import requests
import base64
from flask import Flask, request
from multiprocessing import Process, Pipe
import ecdsa
import random

from miner_config import *

import logging
log = logging.getLogger('werkzeug')
log.setLevel(logging.ERROR)

node = Flask(__name__)


class Block:
    def __init__(self, index, timestamp, data, previous_hash):
        """Returns a new Block object. Each block is "chained" to its previous
        by calling its unique hash.

        Args:
            index (int): Block number.
            timestamp (int): Block creation timestamp.
            data (str): Data to be sent.
            previous_hash(str): String representing previous block unique hash.

        Attrib:
            index (int): Block number.
            timestamp (int): Block creation timestamp.
            data (str): Data to be sent.
            previous_hash(str): String representing previous block unique hash.
            hash(str): Current block unique hash.

        """
        self.index = index
        self.timestamp = timestamp
        self.data = data
        self.previous_hash = previous_hash
        self.hash = self.hash_block()

    def __eq__(self, other):
        return self.hash == other.hash

    def hash_block(self):
        """Creates the unique hash for the block. It uses sha256."""
        sha = hashlib.sha256()
        string_to_hash = str(self.index) + str(self.timestamp) + str(self.previous_hash)

        for key, val in sorted(self.data.items()):
            string_to_hash += str(key) + str(val) + '_'

        print("=======================+")
        print(self.index)
        print(string_to_hash)
        print()

        sha.update(string_to_hash.encode('utf-8'))
        return sha.hexdigest()


def create_genesis_block():
    """To create each block, it needs the hash of the previous one. First
    block has no previous, so it must be created manually (with index zero
     and arbitrary previous hash)"""
    return Block(0, time.time(), {
        "proof-of-work": True,
        "transactions": None},
        "0")


def create_block(d):
    print("in create_block()")
    for key, val in d.items():
        print(key, val)
    print()
    return Block(d['index'], d['timestamp'], d['data'], d.get('previous_hash', ''))


# Node's blockchain copy
BLOCKCHAIN = [create_genesis_block()]

# Server's blockchain
BLOCKCHAIN2 = BLOCKCHAIN[:]

""" Stores the transactions that this node has in a list.
If the node you sent the transaction adds a block
it will get accepted, but there is a chance it gets
discarded and your transaction goes back as if it was never
processed"""
NODE_PENDING_TRANSACTIONS = []


# def proof_of_work(last_proof, blockchain):
#     # Creates a variable that we will use to find our next proof of work
#     incrementer = last_proof + 1
#     # Keep incrementing the incrementer until it's equal to a number divisible by 7919
#     # and the proof of work of the previous block in the chain
#     start_time = time.time()
#     while not (incrementer % 7919 == 0 and incrementer % last_proof == 0):
#         incrementer += 1
#         # Check if any node found the solution every 60 seconds
#         if int((time.time()-start_time) % 60) == 0:
#             # If any other node got the proof, stop searching
#             new_blockchain = consensus(blockchain)
#             if new_blockchain:
#                 # (False: another node got proof first, new blockchain)
#                 return False, new_blockchain
#     # Once that number is found, we can return it as a proof of our work
#     return incrementer, blockchain


def proof_of_work(a=None): 
    time_to_sleep = random.randint(2, 5)

    for i in range(time_to_sleep):
        time.sleep(1)
        new_blockchain = consensus(a)
        if new_blockchain:
            print("SWITCHING TO ANOTHER CHAIN", BLOCKCHAIN[-1].index)
            return False

    return True


def mine(a):
    global BLOCKCHAIN

    print("Mine init.")
    # for block in BLOCKCHAIN:
        # if type(block) != Block:
        #     block['data'] = json.loads(block['data'])

    while True:
        """Mining is the only way that new coins can be created.
        In order to prevent too many coins to be created, the process
        is slowed down by a proof of work algorithm.
        """
        # Get the last proof of work
        # print(BLOCKCHAIN)
        last_block = BLOCKCHAIN[-1]

        # Find the proof of work for the current block being mined
        # Note: The program will hang here until a new proof of work is found
        proof = proof_of_work(a)
        # If we didn't guess the proof, start mining again
        if not proof:
            # Update blockchain and save it to file
            print('recvd blockchain of length', len(BLOCKCHAIN))
            # BLOCKCHAIN = proof[1]
            # a.send(BLOCKCHAIN)
            # requests.get(url = config['MINER_NODE_URL'] + '/blocks', params = {'update':config['MINER_ADDRESS']})
            # continue

        else:
            print('mined block')
            # Once we find a valid proof of work, we know we can mine a block so
            # ...we reward the miner by adding a transaction
            # First we load all pending transactions sent to the node server
            print('=================================> running @', config['MINER_NODE_URL'] + '/txion')
            pending_transactions = requests.get(url = config['MINER_NODE_URL'] + '/txion', params = {'update':config['MINER_ADDRESS']}).content
            pending_transactions = json.loads(pending_transactions)
            # Then we add the mining reward
            pending_transactions.append({
                "from": "network",
                "to": config['MINER_ADDRESS'],
                "amount": 1})
            # Now we can gather the data needed to create the new block
            new_block_data = {
                "proof-of-work": proof,
                "transactions": list(pending_transactions)
            }
            new_block_index = int(last_block.index) + 1
            new_block_timestamp = time.time()
            last_block_hash = last_block.hash

            # Now create the new block
            mined_block = Block(new_block_index, new_block_timestamp, new_block_data, last_block_hash)
            BLOCKCHAIN.append(mined_block)
            # Let the client know this node mined a block
            print(json.dumps({
              "index": new_block_index,
              "timestamp": str(new_block_timestamp),
              "data": new_block_data,
              "previous_hash": last_block_hash
            }, sort_keys=True) + "\n")

        a.send(BLOCKCHAIN)
        requests.get(url = config['MINER_NODE_URL'] + '/blocks', params = {'update': config['MINER_ADDRESS']})


def serialize_data(blockchain_str):
    # print("packed:", blockchain_str)
    blockchain_str = json.loads(blockchain_str)
    # print("loaded:", blockchain_str)
    unpacked_blockchain = []
    for block in blockchain_str:
        block['data'] = ast.literal_eval(block['data'])
        last_block = create_block(block)
        # last_block.data = last_block.data.replace('\'', '"')
        # print('before:', last_block.data)
        # last_block.data = json.loads(last_block.data)
        # print('after:', last_block.data)
        unpacked_blockchain.append(last_block)
    # print("unpacked:", unpacked_blockchain)
    return unpacked_blockchain

def find_new_chains():
    # Get the blockchains of every other node
    other_chains = []
    for node_url in config['PEER_NODES']:
        # Get their chains using a GET request
        try:
            rcv_blockchain = requests.get(url = node_url + "/blocks").content
            unpacked_blockchain = serialize_data(rcv_blockchain)
            
            # Verify other node block is correct
            validated = validate_blockchain(unpacked_blockchain)
            if validated:
                # Add it to our list
                other_chains.append(unpacked_blockchain)
        except Exception as e:
            print(e)
            pass

    return other_chains


def consensus(a=None):
    global BLOCKCHAIN

    # Get the blocks from other nodes
    other_chains = find_new_chains()
    # If our chain isn't longest, then we store the longest chain
    longest_chain = BLOCKCHAIN[:]
    changed = False

    for chain in other_chains:
        # print("rcvd ", chain[-1].index)
        if len(longest_chain) < len(chain):
            longest_chain = chain[:]
            changed = True

    # If the longest chain wasn't ours, then we set our chain to the longest
    if not changed:
        # Keep searching for proof
        return False
    else:
        print("longest chain: ", longest_chain[-1].hash)
        print("my chain: ", BLOCKCHAIN[-1].hash)
        # Give up searching proof, update chain and start over again
        BLOCKCHAIN = longest_chain[:]
        a.send(BLOCKCHAIN)
        return True


def validate_blockchain(block):
    """Validate the submitted chain. If hashes are not correct, return false
    block(str): json
    """
    return True


@node.route('/blocks', methods=['GET'])
def get_blocks():
    global BLOCKCHAIN2
    # Load current blockchain. Only you should update your blockchain
    if request.args.get("update") == config['MINER_ADDRESS']:
        BLOCKCHAIN2 = pipe_input.recv()

    chain_to_send = BLOCKCHAIN2
    # Converts our blocks into dictionaries so we can send them as json objects later
    chain_to_send_json = []
    for block in chain_to_send:
        if type(block) != Block:
            block = create_block(block)

        block = {
            "index": str(block.index),
            "timestamp": str(block.timestamp),
            "data": str(block.data),
            "hash": block.hash,
            "previous_hash": block.previous_hash
        }
        chain_to_send_json.append(block)

    # Send our chain to whomever requested it
    chain_to_send = json.dumps(chain_to_send_json, sort_keys=True)
    return chain_to_send


@node.route('/txion', methods=['GET', 'POST'])
def transaction():
    """Each transaction sent to this node gets validated and submitted.
    Then it waits to be added to the blockchain. Transactions only move
    coins, they don't create it.
    """

    global NODE_PENDING_TRANSACTIONS

    if request.method == 'POST':
        # On each new POST request, we extract the transaction data
        new_txion = request.get_json()
        # Then we add the transaction to our list
        if validate_signature(new_txion['from'], new_txion['signature'], new_txion['message']):
            NODE_PENDING_TRANSACTIONS.append(new_txion)
            # Because the transaction was successfully
            # submitted, we log it to our console
            print("New transaction")
            print("FROM: {0}".format(new_txion['from']))
            print("TO: {0}".format(new_txion['to']))
            print("AMOUNT: {0}\n".format(new_txion['amount']))
            # Then we let the client know it worked out
            return "Transaction submission successful\n"
        else:
            return "Transaction submission failed. Wrong signature\n"
    # Send pending transactions to the mining process
    elif request.method == 'GET' and request.args.get("update") == config['MINER_ADDRESS']:
        pending = json.dumps(NODE_PENDING_TRANSACTIONS, sort_keys=True)

        # Empty transaction list
        NODE_PENDING_TRANSACTIONS = []

        return pending


def validate_signature(public_key, signature, message):
    """Verifies if the signature is correct. This is used to prove
    it's you (and not someone else) trying to do a transaction with your
    address. Called when a user tries to submit a new transaction.
    """
    public_key = (base64.b64decode(public_key)).hex()
    signature = base64.b64decode(signature)
    vk = ecdsa.VerifyingKey.from_string(bytes.fromhex(public_key), curve=ecdsa.SECP256k1)
    # Try changing into an if/else statement as except is too broad.
    try:
        return vk.verify(signature, message.encode())
    except:
        return False


def welcome_msg():
    print("""       =========================================\n
        OUR COIN v1.0.0 - BLOCKCHAIN SYSTEM\n
       =========================================\n\n
        You can find more help at: https://github.com/cosme12/SimpleCoin\n
        Make sure you are using the latest version or you may end in
        a parallel chain.\n\n\n""")


if __name__ == '__main__':
    welcome_msg()

    config = configs[sys.argv[1]]

    # Start mining
    pipe_output, pipe_input = Pipe()
    miner_process = Process(target=mine, args=(pipe_output,))
    miner_process.start()

    # Start server to receive transactions
    transactions_process = Process(target=node.run(host='0.0.0.0', port=config['MINER_NODE_PORT']), args=pipe_input)
    transactions_process.start()
