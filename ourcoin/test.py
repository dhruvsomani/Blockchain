from bls import *

def test_multi_authorities():
	m = [10,20,30,40,50]
	n = 5 # number of authorities
	params = setup()

	# generate key
	(sk, vk) = keygen(params, n)

	# sign all the messages
	sigs = [sign(params, ski, [mi]) for ski,mi in zip(sk,m)]

	# aggregate credentials
	sigma = aggregate_sigma(params, sigs)

	assert aggregate_verify(params, sigma, vk, m)
	
test_multi_authorities()