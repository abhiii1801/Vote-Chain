from flask import Flask, request, jsonify, render_template, redirect, url_for, session, flash
import sqlite3
from web3 import Web3
import random
import datetime

app = Flask(__name__)
app.secret_key = 'your_secret_key'
DATABASE = 'users.db'
ADMIN_PRIVATE_KEY = '784002c9ea4fd1fc96673135515484e067c2dedd609ba7973e1142ae0497c829'
ADMIN_ADDRESS = '0xCD8BD9b81ea917C727d3f11cB9B7F68060c1Fb9b'

w3 = Web3(Web3.HTTPProvider('http://127.0.0.1:7545'))

contract_address = '0xE360aA77BB36134719145C13082cEf78fe5B10E1'
contract_abi ='''[
	{
		"inputs": [],
		"stateMutability": "nonpayable",
		"type": "constructor"
	},
	{
		"inputs": [
			{
				"internalType": "string",
				"name": "_name",
				"type": "string"
			}
		],
		"name": "addParty",
		"outputs": [],
		"stateMutability": "nonpayable",
		"type": "function"
	},
	{
		"inputs": [],
		"name": "admin",
		"outputs": [
			{
				"internalType": "address",
				"name": "",
				"type": "address"
			}
		],
		"stateMutability": "view",
		"type": "function"
	},
	{
		"inputs": [],
		"name": "getPartyNames",
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
		"name": "getResults",
		"outputs": [
			{
				"components": [
					{
						"internalType": "string",
						"name": "name",
						"type": "string"
					},
					{
						"internalType": "uint256",
						"name": "voteCount",
						"type": "uint256"
					}
				],
				"internalType": "struct Voting.Party[]",
				"name": "",
				"type": "tuple[]"
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
		"name": "hasVoted",
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
		"name": "parties",
		"outputs": [
			{
				"internalType": "string",
				"name": "name",
				"type": "string"
			},
			{
				"internalType": "uint256",
				"name": "voteCount",
				"type": "uint256"
			}
		],
		"stateMutability": "view",
		"type": "function"
	},
	{
		"inputs": [],
		"name": "toggleVoting",
		"outputs": [
			{
				"internalType": "bool",
				"name": "",
				"type": "bool"
			}
		],
		"stateMutability": "nonpayable",
		"type": "function"
	},
	{
		"inputs": [
			{
				"internalType": "uint256",
				"name": "_partyIndex",
				"type": "uint256"
			}
		],
		"name": "vote",
		"outputs": [],
		"stateMutability": "nonpayable",
		"type": "function"
	},
	{
		"inputs": [],
		"name": "votingStarted",
		"outputs": [
			{
				"internalType": "bool",
				"name": "",
				"type": "bool"
			}
		],
		"stateMutability": "view",
		"type": "function"
	}
]'''

contract = w3.eth.contract(address=contract_address, abi=contract_abi)

def get_db_connection():
    conn = sqlite3.connect(DATABASE)
    conn.row_factory = sqlite3.Row
    return conn


@app.route('/')
def index():
    return render_template('index.html')


@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        data = request.get_json()
        username = data['username']
        password = data['password']
        
        conn = get_db_connection()
        user = conn.execute("SELECT * FROM users WHERE username = ? AND password = ?", (username, password)).fetchone()
        conn.close()

        if user:
            session['user_id'] = user['id']
            session['role'] = user['role']
            
            redirect_url = url_for('admin_panel' if user['role'] == 'admin' else 'vote_panel')
            return jsonify({'redirect': redirect_url})
        else:
            return jsonify({'error': 'Invalid username or password'})
        
    return render_template('login.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        data = request.get_json()
        name = data['name']
        password = data['password']
        wallet_id = data['wallet_id']
        private_key = data['private_key']

        username = name.lower().replace(' ', '_') + '_' + str(random.randint(1000, 9999))

        conn = get_db_connection()
        try:
            conn.execute('INSERT INTO users (username, name, password, wallet_id, private_key) VALUES (?, ?, ?, ?, ?)',
                         (username, name, password, wallet_id, private_key))
            conn.commit()
            return jsonify({'message': 'success', 'user_id': username})
        except sqlite3.IntegrityError as e:
            return jsonify({'error': str(e)}), 400
        finally:
            conn.close()

    return render_template('register.html')

@app.route('/admin_panel')
def admin_panel():
    if 'user_id' not in session or session['role'] != 'admin':
        print("Not admin")
        return redirect(url_for('login'))
    print("Admin Login")
    return render_template('admin.html')

@app.route('/vote_panel', methods=['GET'])
def vote_panel():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    
    parties = contract.functions.getPartyNames().call()
    return render_template('vote.html', parties=parties)

@app.route('/add_party', methods=['POST'])
def add_party():
    if 'user_id' not in session or session['role'] != 'admin':
        return redirect(url_for('login'))
    
    data = request.json
    party_name = data['name']

    print(f"[SERVER]: {party_name} received !!!")
    try:
        tx = contract.functions.addParty(party_name).build_transaction({
            'chainId': 1337,
            'gas': 2000000,
            'gasPrice': w3.to_wei('50', 'gwei'),
            'nonce': w3.eth.get_transaction_count(ADMIN_ADDRESS),
        })

        signed_tx = w3.eth.account.sign_transaction(tx, private_key=ADMIN_PRIVATE_KEY)
        tx_hash = w3.eth.send_raw_transaction(signed_tx.rawTransaction)

        print(f"[SERVER]: partyName {party_name} added !!!")
        print(f"[SERVER]: Hash: {tx_hash.hex()}")

        return jsonify({'message': 'success'})
    except Exception as e:
        print(e)
        return jsonify({'error': 'error'})

@app.route('/vote', methods=['POST'])
def vote():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    
    data = request.json
    party_index = int(data['party_index'])

    print(f"[SERVER]: partyindex {party_index} received !!!")

    conn = get_db_connection()
    user = conn.execute("SELECT wallet_id, private_key FROM users WHERE id = ?", (session['user_id'],)).fetchone()
    conn.close()

    if user is None:
        return jsonify({'message': 'User not found'}), 404

    voter_address = user['wallet_id']
    private_key = user['private_key']

    print(f"[SERVER]: voter_address {voter_address} {private_key} received !!!")

    try: 
        print("party_index", party_index)
        tx = contract.functions.vote(party_index).build_transaction({
            'chainId': 1337, 
            'gas': 2000000,
            'gasPrice': w3.to_wei('50', 'gwei'),
            'nonce': w3.eth.get_transaction_count(voter_address),
        })

        signed_tx = w3.eth.account.sign_transaction(tx, private_key=private_key)
        tx_hash = w3.eth.send_raw_transaction(signed_tx.rawTransaction)

        print(f"[SERVER]: VOTED !!!")
        print(f"[SERVER]: tx_hash {tx_hash.hex()} received !!!")

        return jsonify({'message': 'success'})
    
    except Exception as e:
        print(f"[SERVER]: errrror :{e}")
        return jsonify({'message': 'You have already Voted'})

@app.route('/results', methods=['GET'])
def results():
    if 'user_id' not in session or session['role'] != 'admin':
        return redirect(url_for('login'))
    
    results = contract.functions.getResults().call()
    return render_template('results.html', results=results)

@app.route('/toggle_voting', methods=['POST'])
def toggle_voting():
    if 'user_id' not in session or session['role'] != 'admin':
        return redirect(url_for('login'))

    print("[SERVER]: Toggling voting !!!")

    try:
        # Build and send the transaction to toggle voting
        tx = contract.functions.toggleVoting().build_transaction({
            'chainId': 1337,
            'gas': 2000000,
            'gasPrice': w3.to_wei('50', 'gwei'),
            'nonce': w3.eth.get_transaction_count(ADMIN_ADDRESS),
        })

        signed_tx = w3.eth.account.sign_transaction(tx, private_key=ADMIN_PRIVATE_KEY)
        tx_hash = w3.eth.send_raw_transaction(signed_tx.rawTransaction)

        receipt = w3.eth.wait_for_transaction_receipt(tx_hash)

        voting_status = contract.functions.votingStarted().call()
        if voting_status:
            print("Voting On")
        else:
            print("Voting OFF")

        return jsonify({'transaction_hash': tx_hash.hex(), 'voting_status': voting_status})
    
    except Exception as e:
        print(f"[SERVER]: {e}")
        return jsonify({'error': str(e)})

@app.route('/logout')
def logout():
    session.pop('user_id', None)
    session.pop('role', None)
    return redirect(url_for('index'))

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)