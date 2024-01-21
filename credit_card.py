import json
import base64
import time
import random

from algosdk.v2client import algod, indexer
from algosdk import account, encoding, mnemonic, transaction
from pyteal import *

# Algod client configuration
algod_address = "http://localhost:4001"
algod_token = "a"*64
algod_client = algod.AlgodClient(algod_token, algod_address)

local_schema = transaction.StateSchema(num_uints=6, num_byte_slices=6)
global_schema = transaction.StateSchema(num_uints=6, num_byte_slices=6)

cibil = random.randint(550,900)

with open("approval_program.teal", "r") as f:
    approval_program = f.read()

with open("clear_program.teal", "r") as f:
    clear_program = f.read()

params = algod_client.suggested_params()
note = "Credit Approval".encode()
amount = 0
mnemonic_secret = "wheel genre pistol swing cool thumb office divert arrow cable fall guess spatial habit salute tragic elite world candy shift sad monkey captain ability cotton"
contract_private_key = mnemonic.to_private_key(mnemonic_secret)
contract_address = account.address_from_private_key(contract_private_key)

approval_result = algod_client.compile(approval_program)
approval_binary = base64.b64decode(approval_result["result"])

clear_result = algod_client.compile(clear_program)
clear_binary = base64.b64decode(clear_result["result"])

on_complete = transaction.OnComplete.NoOpOC.real

sp = algod_client.suggested_params()

start_txn = transaction.ApplicationCreateTxn(
    contract_address,
    sp,
    on_complete,
    approval_program=approval_binary,
    clear_program=clear_binary,
    global_schema=global_schema,
    local_schema=local_schema,
)

mnemonic_secret = "motor since ramp tragic antique spare salmon glide spoil board alien bus wrist club symptom hello wine year unit vital pave sense rebel abandon worth"
alice_private_key = mnemonic.to_private_key(mnemonic_secret)
alice_address = account.address_from_private_key(alice_private_key)

txn_1 = transaction.PaymentTxn(contract_address, params, contract_address, 0, None, note)

gid = transaction.calculate_group_id([start_txn, txn_1])
start_txn.group = gid
txn_1.group = gid

txn = start_txn.sign(contract_private_key)
txn_1 = txn_1.sign(contract_private_key)

txid = algod_client.send_transactions([txn,txn_1])
print("transaction id: ",txid,'\n')

time.sleep(10)

res = algod_client.account_info(contract_address)
apps = res["created-apps"]
appid = apps[-1]['id']
print("Application ID: ",appid,'\n')

print('\n')

def opt_in_app(client, private_key, index, rec):
    # declare sender
    sender = account.address_from_private_key(private_key)
    receiver = account.address_from_private_key(rec)

    params = client.suggested_params()
    params.flat_fee = True
    params.fee = 1000

    txn = transaction.ApplicationOptInTxn(sender, params, index, app_args = ["card",cibil])

    signed_txn = txn.sign(private_key)
    tx_id = client.send_transaction(signed_txn)
    print(tx_id)
    time.sleep(10)

def format_state(state):
    formatted = {}
    for item in state:
        key = item["key"]
        value = item["value"]
        formatted_key = base64.b64decode(key).decode("utf-8")
        if value["type"] == 1:
            if formatted_key == "c":
                formatted_value = base64.b64decode(value["bytes"]).decode("utf-8")
            else:
                formatted_value = value["bytes"]
            formatted[formatted_key] = formatted_value
        else:
            formatted[formatted_key] = value["uint"]
    return formatted

def credit_approval():
    result = algod_client.account_info(contract_address)
    apps_created = result["created-apps"]
    for app in apps_created:
        if app["id"] == appid:
            res = format_state(app["params"]["global-state"])
            break
    return res

opt_in_app(algod_client, alice_private_key, appid, contract_private_key)  
res = credit_approval()

approval_val = res["approval"]
hex_val = hex(approval_val)[2:]
bytes_value = bytes.fromhex(hex_val)
string_value = bytes_value.decode()
print(f"card approved: {string_value}")

if string_value == 'Yes':
    print("Credit card approved. Congratulations!!!!")
else:
    print("Unfortunately the card is not approved")
