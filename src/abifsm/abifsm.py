import re, os, json
from collections import Counter
from web3 import Web3 as w3
from difflib import ndiff, unified_diff
import requests as r

import os 

os.environ['ABI_URL'] = 'https://storage.googleapis.com/agora-abis/v2'


import requests as r

def camel_to_snake(name):
    # Handle acronyms followed by a lowercase letter and acronyms at the start
    snake_case = re.sub(r'([A-Z]+)([A-Z][a-z])', r'\1_\2', name)  # Handles acronyms followed by non-acronyms
    snake_case = re.sub(r'([a-z\d])([A-Z])', r'\1_\2', snake_case)  # Handles camelCase transitions
    return snake_case.lower().lstrip('_')

def make_literal_signature(input_type):

    if input_type['type'] == 'tuple':
        typ = ",".join(make_literal_signature(t) for t in input_type['components'])
        return f"({typ})"
    elif input_type['type'] == 'tuple[]':
        typ = ",".join(make_literal_signature(t) for t in input_type['components'])
        return f"({typ})[]"
    else:
        return input_type['type']

class Fragment:
    def __init__(self, abi_label, literal):
        self.abi_label = abi_label
        self.literal = literal
        self.type = literal['type']
        self.name = literal.get('name', None)
        self.inputs = literal.get('inputs', None)

        params = ",".join([make_literal_signature(param) for param in self.literal.get('inputs', [])])

        self.signature = f"{self.name}({params})"
        self.topic = w3.keccak(text=self.signature).hex()
        self.topic = self.topic.replace("0x", "")

        if self.name:
            self.slug = camel_to_snake(self.name)
        else:
            self.slug = None
        
        self.include_topic = None

    def cropped_slug(self, max_len):

        if self.include_topic:
            full = self.slug[:max_len + 8]
            topic = str(self.topic)
            full += f"_{topic[:8]}"
        else:
            full = self.slug[:max_len]
        
        return full[:max_len]
    
    @property
    def fields(self):
        return [o['name'] for o in self.inputs]

    

class ABI:
    def __init__(self, label, abi_json):
        self.label = label
        self.fragments = [Fragment(label, frag) for frag in abi_json]
        self.fragments.sort(key=lambda x: str(x.name) + x.topic)
        self.counts = Counter([frag.name for frag in self.fragments if frag.type == 'event'])

        for fragment in self.fragments:
            fragment.include_topic = self.counts[fragment.name] > 1

    def __len__(self):
        return len(self.fragments)

    def is_proxy(self):
        
        signatures = {fragment.signature for fragment in self.fragments}

        return set(['implementation()', 'upgradeTo(address)']).issubset(signatures)

    @staticmethod    
    def from_file(label, fname):

        with open(fname) as f:
            abi_json = json.load(f)
            return ABI(label, abi_json)

    @staticmethod    
    def from_url(label, url):

        resp = r.get(url)
        abi_json = resp.json()
        return ABI(label, abi_json)

    @staticmethod    
    def from_internet(label, address, chain_id, url=None, check=True, implementation=False):

        if url is None:
            url = os.getenv('ABI_URL')
        
        if check:
            address = w3.to_checksum_address(address)

        # if implementation:
        #     if address.lower() == '0xcDF27F107725988f2261Ce2256bDfCdE8B382B10'.lower():
        #        address = '0xecbf4ed9f47302f00f0f039a691e7db83bdd2624'

        full_url = url + f"/{chain_id}/checked/" + address + ".json"
        try:
            abi_json = r.get(full_url).json()
        except:
            raise Exception(f"ABI not found for {address} @ {full_url}.")

        potential_abi = ABI(label, abi_json)

        if potential_abi.is_proxy() and implementation:

            if chain_id == 10:

                optimism_rpc = "https://mainnet.optimism.io"
                web3 = w3(w3.HTTPProvider(optimism_rpc))
                proxy_address = w3.to_checksum_address(address)

                # EIP-1967 implementation storage slot
                IMPLEMENTATION_SLOT = "0x360894A13BA1A3210667C828492DB98DCA3E2076CC3735A920A3CA505D382BBC"

                storage_data = web3.eth.get_storage_at(proxy_address, IMPLEMENTATION_SLOT)

                implementation_address = storage_data[-20:].hex()

                print(f"Warning: Returning ABI for implementation '{implementation_address}', rather than ABI for '{address}.")

                return ABI.from_internet(label, implementation_address, chain_id, url=url, check=check)
            
            else:
                raise Exception(f"implementation=True is not supported for chain ID# {chain_id}.")

        return potential_abi

class ABISet:
    def __init__(self, name, abis):
        self.name = name
        self.abis = abis

    @property
    def events(self):
        for abi in self.abis:
            for fragment in abi.fragments:
                if fragment.type == 'event':
                    yield fragment

    @property
    def unique_events(self):

        already_returned = []

        for abi in self.abis:
            for fragment in abi.fragments:
                if fragment.type == 'event':
                    if fragment.signature not in already_returned:
                        already_returned.append(fragment.signature)
                        yield fragment

    @property
    def fragments(self):
        for abi in self.abis:
            for fragment in abi.fragments:
                yield fragment

    def get_pgtable_by_signature(self, signature):

        event = self.get_by_signature(signature)

        return self.pgtable(event)

    def get_pgtable_by_name(self, name):

        event = self.get_by_name(name)

        return self.pgtable(event)
    
    def get_by_topic(self, key):

        for event in self.events:
            if (event.topic == key) or (event.topic[:len(key)] == key):
                return event

    def get_by_name(self, key, pos=0):

        for event in self.events:
            if (str(event.slug) == key) or (str(event.name) == key):
                if pos == 0:
                    return event
                else:
                    pos = pos - 1

    def get_by_signature(self, key, pos=0):

        for event in self.events:
            if event.signature == key:
                if pos == 0:
                    return event
                else:
                    pos = pos - 1

    def pgtable(self, event, check=True):

        prefix = self.name + '_' + event.abi_label + '_'

        out = prefix + event.cropped_slug(63 - len(prefix))

        if check:
            for other_event in self.events:
                if str(event.topic) != str(other_event.topic):
                    if self.pgtable(other_event, check=False) == out:
                        raise Exception(f"Postgres Table {out} is not unique enough.")
        
        return out
    
    def pgtables(self, sort=False):

        tables = [self.pgtable(event) for event in self.events]

        if sort:
            tables.sort()
        
        for table in tables:
            yield table
    
    def __len__(self):
        return sum([len(abi) for abi in self.abis])

    def compare_tables(self, other, printit=True):

        self_tables = list(self.pgtables())
        other_tables = list(other.pgtables())

        diff = ndiff(self_tables, other_tables)

        if printit:
            print("\n")
            print('\n'.join(diff), end="\n")

        return diff

    def compare_signatures(self, other, printit=True):

        self_signatures = [f.signature for f in self.fragments]
        othr_signatures = [f.signature for f in other.fragments]

        diff = ndiff(self_signatures, othr_signatures)

        if printit:
            print("\n")
            print('\n'.join(diff), end="\n")

        return diff

    def compare_events(self, other, printit=True):

        self_events = [e.signature for e in self.events]
        othr_events = [e.signature for e in other.events]

        diff = ndiff(self_events, othr_events)

        if printit:
            print("\n")
            print('\n'.join(diff), end="\n")

        return diff
    
class FQPGSqlGen:
    def __init__(self, abis, schema=None):
        self.abis = abis
        self.schema = schema

    def __getitem__(self, key):

        event = None
        event_by_name = None
        event_by_topic = None

        try:
            event_by_name = self.abis.get_by_name(key)
        except:
            pass
        
        try:
            event_by_topic = self.abis.get_by_topic(key)
        except:
            pass

        event = event_by_name or event_by_topic

        if event is None:
            raise KeyError(f"No ABI found for {key}")
        
        if self.schema:
            return self.schema + "." + self.abis.pgtable(event)
        else:
            return self.abis.pgtable(event)

if __name__ == '__main__':


    if False:
        new = ABI.from_internet('testOPGov@t=0', '0x3f6837964616a0c8853b1a38b2bbdb08dae5fc48')
        new = ABISet('new', [new])
        old = ABI.from_internet('testOPGov@t=-1', '0xe4e2ec9cd41a672de3925a1e39b658367a99b1ef')
        old = ABISet('old', [old])

        diff = old.compare_signatures(new)

        both = ABISet('both', [new, old])


        out = []
        for event in both.unique_events:
            print(event)
            out.append(event.literal)

        import json
        print(json.dumps(out))
    
    if True:



        new = ABI.from_file('new', '/Users/jm/code/tenants/abis/0x2b7a5fbba87ebb3089525d5fd61b914a6656ff6b.json')
        new = ABISet('new', [new])
        old = ABI.from_internet('old', '0x2b7a5fbba87ebb3089525d5fd61b914a6656ff6b')
        old = ABISet('old', [old])

        diff = old.compare_signatures(new)

