import re, os, json
from collections import Counter
from web3 import Web3 as w3

import requests as r

def camel_to_snake(name):
    # Handle acronyms followed by a lowercase letter and acronyms at the start
    snake_case = re.sub(r'([A-Z]+)([A-Z][a-z])', r'\1_\2', name)  # Handles acronyms followed by non-acronyms
    snake_case = re.sub(r'([a-z\d])([A-Z])', r'\1_\2', snake_case)  # Handles camelCase transitions
    return snake_case.lower().lstrip('_')


class Fragment:
    def __init__(self, abi_label, literal):
        self.abi_label = abi_label
        self.literal = literal
        self.type = literal['type']
        self.name = literal.get('name', None)
        self.inputs = literal.get('inputs', None)

        params = ",".join([param['type'] for param in self.literal.get('inputs', [])])
        self.signature = f"{self.name}({params})"
        self.topic = w3.keccak(text=self.signature).hex()

        if self.name:
            self.slug = camel_to_snake(self.name)
        else:
            self.slug = None
        
        self.include_topic = None

    def cropped_slug(self, max_len):

        if self.include_topic:
            full = self.slug[:max_len + 8]
            full += f"_{self.topic[:8]}"
        else:
            full = self.slug[:max_len]
        
        return full[:max_len]
    

class ABI:
    def __init__(self, label, fragments):
        self.label = label
        self.fragments = fragments
        self.fragments.sort(key=lambda x: str(x.name) + x.topic)
        self.counts = Counter([frag.name for frag in fragments if frag.type == 'event'])

        for fragment in self.fragments:
            fragment.include_topic = self.counts[fragment.name] > 1

    @staticmethod    
    def from_file(label, fname):

        with open(fname) as f:
            abi_json = json.load(f)
            return ABI(label, [Fragment(label, frag) for frag in abi_json])

    @staticmethod    
    def from_internet(label, address, url=None, check=True):

        if url is None:
            url = os.getenv('ABI_URL')

        if check:
            address = w3.to_checksum_address(address)

        abi_json = r.get(url + address + ".json").json()

        return ABI(label, abi_json)

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
    
    def pgtable(self, event, check=True):

        prefix = self.name + '_' + event.abi_label + '_'

        out = prefix + event.cropped_slug(63 - len(prefix))

        if check:
            for other_event in self.events:
                if str(event.topic) != str(other_event.topic):
                    if self.pgtable(other_event, check=False) == out:
                        raise Exception(f"Postgres Table {out} is not unique enough.")
        
        return out
    
    

    

