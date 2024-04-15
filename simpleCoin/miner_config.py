"""Configure this file before you start mining. Check wallet.py for
more details.
"""

configs = {
	"config1": {
		# Write your generated adress here. All coins mined will go to this address
		"MINER_ADDRESS" : "q3nf394hjg-random-miner-address-34nf3i4nfldhruv",

		# Write your node url or ip. If you are running it localhost use default
		"MINER_NODE_URL" : "http://localhost:5000",
		"MINER_NODE_PORT" : 5000,

		# Store the url data of every other node in the network
		# so that we can communicate with them
		"PEER_NODES" : ["http://localhost:5001"],
	},

	"config2": {
		# Write your generated adress here. All coins mined will go to this address
		"MINER_ADDRESS" : "q3nf394hjg-random-miner-address-34nf3i4nflviraj",

		# Write your node url or ip. If you are running it localhost use default
		"MINER_NODE_URL" : "http://localhost:5001",
		"MINER_NODE_PORT" : 5001,

		# Store the url data of every other node in the network
		# so that we can communicate with them
		"PEER_NODES" : ["http://localhost:5000"],
	}
}
