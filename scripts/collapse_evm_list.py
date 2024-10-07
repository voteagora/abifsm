
import json

def make_symbol(name):

    slug = name.lower()

    for char in ['.', '-', '_', ' ']:
        slug = slug.replace(char, '')

    return slug


chain_ids = {}
with open('/Users/jm/code/abifsm/src/abifsm/evm_chainlist_raw.json', 'r') as f:
    data = json.load(f)

    for chain in data:
        #print(chain['name'])

        chain['chainId']

        row = {'name' : chain['name'], 'slug' : make_symbol(chain['shortName'])}

        chain_ids[chain['chainId']] = row

        # print(row)

print(chain_ids)
        
