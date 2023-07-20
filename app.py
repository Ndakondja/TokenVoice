from sys import exception
from flask import Flask, render_template, request

from web3 import Web3

# Create an instance of the Web3 class and connect to the local Ethereum node
w3 = Web3(Web3.HTTPProvider('http://localhost:8545'))

# Check the connection status
if w3.is_connected():
    print('Connected to local Ethereum node')
else:
    print('Failed to connect to local Ethereum node')

# Example: Get the latest block number
block_number = w3.eth.block_number
print(f'Latest block number: {block_number}')
print (w3.is_connected())


# Address and ABI of the deployed voting contract
contract_address = '0x8917bE5767B3431689BEb50685eAA783AcD8C5A6'
contract_abi = [
	{
		"inputs": [
			{
				"internalType": "string[]",
				"name": "_candidates",
				"type": "string[]"
			}
		],
		"stateMutability": "nonpayable",
		"type": "constructor"
	},
	{
		"inputs": [
			{
				"internalType": "uint256",
				"name": "candidateIndex",
				"type": "uint256"
			}
		],
		"name": "vote",
		"outputs": [],
		"stateMutability": "nonpayable",
		"type": "function"
	},
	{
		"inputs": [
			{
				"internalType": "uint256",
				"name": "",
				"type": "uint256"
			}
		],
		"name": "candidateList",
		"outputs": [
			{
				"internalType": "string",
				"name": "",
				"type": "string"
			}
		],
		"stateMutability": "view",
		"type": "function"
	},
	{
		"inputs": [],
		"name": "getAllCandidates",
		"outputs": [
			{
				"internalType": "string[]",
				"name": "",
				"type": "string[]"
			}
		],
		"stateMutability": "view",
		"type": "function"
	},
	{
		"inputs": [],
		"name": "getCandidateCount",
		"outputs": [
			{
				"internalType": "uint256",
				"name": "",
				"type": "uint256"
			}
		],
		"stateMutability": "view",
		"type": "function"
	},
	{
		"inputs": [
			{
				"internalType": "uint256",
				"name": "candidateIndex",
				"type": "uint256"
			}
		],
		"name": "getVoteCount",
		"outputs": [
			{
				"internalType": "uint256",
				"name": "",
				"type": "uint256"
			}
		],
		"stateMutability": "view",
		"type": "function"
	},
	{
		"inputs": [
			{
				"internalType": "address",
				"name": "",
				"type": "address"
			}
		],
		"name": "voters",
		"outputs": [
			{
				"internalType": "bool",
				"name": "",
				"type": "bool"
			}
		],
		"stateMutability": "view",
		"type": "function"
	},
	{
		"inputs": [
			{
				"internalType": "uint256",
				"name": "",
				"type": "uint256"
			}
		],
		"name": "votesReceived",
		"outputs": [
			{
				"internalType": "uint256",
				"name": "",
				"type": "uint256"
			}
		],
		"stateMutability": "view",
		"type": "function"
	}
]

# Load the contract
voting_contract = w3.eth.contract(address=contract_address, abi=contract_abi)
# try:
#     print(voting_contract.all_functions())
#     print (voting_contract.functions.getAllCandidates().call())
#     print("*******")

# except Exception as e:
#     print(f"Error occurred: {e}")

# Flask app
app = Flask(__name__)
 
@app.route('/')
def home():
    candidates = voting_contract.functions.getAllCandidates().call()
    print(candidates)  # Add this line
    return render_template('index.html', candidate_list=candidates)

@app.route('/vote', methods=['POST'])
def vote():
    print("in the post")
    candidate_index = int(request.form['candidate_index'])
    account = request.form['account']
    print(account)
    
    transaction = {
        'to': contract_address,  
        'value': 0,  # no ether to send
        'gas': 2000000,
        'gasPrice': w3.to_wei('50', 'gwei'),
        'nonce': w3.eth.get_transaction_count('0x45ddD2E155D8357313655c55b59a4C0b68089D47'),
        'chainId': 702,
        'data': voting_contract.encodeABI(fn_name='vote', args=[candidate_index])  # encode the function call
    }

    private_key = 'd4861dddbbfd8254d2058e19f16491189ce44ed2df4f5ba47c204a11b49c6c17'
    signed_txn = w3.eth.account.sign_transaction(transaction, private_key)
    print(signed_txn)
    result = ''
    try:
        tx_hash = w3.eth.send_raw_transaction(signed_txn.rawTransaction)
        receipt = w3.eth.wait_for_transaction_receipt(tx_hash)
        result = 'Voted Successfully'
    except (exception.ContractLogicError) as e:
        tx_hash = e.transaction_hash
        revert_reason = get_revert_reason(tx_hash)
        result = "Transaction failed: " + revert_reason

    return render_template('vote_result.html', receipt=result)

def get_revert_reason(tx_hash):
    tx = w3.eth.getTransaction(tx_hash)
    result = w3.eth.call({'to': tx['to'], 'data': tx['input']}, block_identifier='latest')
    if result[:10] == '0x08c379a0':  # first 4 bytes of keccak256 hash of "Error(string)"
        length_error_message = int(result[74:138], 16)
        revert_reason = bytes.fromhex(result[138:138+2*length_error_message]).decode()
        return revert_reason
    else:
        return "No revert reason provided or transaction succeeded."
    
@app.route('/results')
def results():
    candidate_list = voting_contract.functions.getAllCandidates().call()
    vote_counts = [voting_contract.functions.getVoteCount(i).call() for i in range(len(candidate_list))]
    return render_template('results.html', candidates=zip(candidate_list, vote_counts))


if __name__ == '__main__':
    app.run(debug=True)
