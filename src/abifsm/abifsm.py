import re, os, json
from collections import Counter
from web3 import Web3 as w3
from difflib import ndiff, unified_diff

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
    def __init__(self, label, abi_json):
        self.label = label
        self.fragments = [Fragment(label, frag) for frag in abi_json]
        self.fragments.sort(key=lambda x: str(x.name) + x.topic)
        self.counts = Counter([frag.name for frag in self.fragments if frag.type == 'event'])

        for fragment in self.fragments:
            fragment.include_topic = self.counts[fragment.name] > 1

    def __len__(self):
        return len(self.fragments)

    @staticmethod    
    def from_file(label, fname):

        with open(fname) as f:
            abi_json = json.load(f)
            return ABI(label, abi_json)

    @staticmethod    
    def from_internet(label, address, url=None, check=True):

        if url is None:
            url = os.getenv('ABI_URL')

        if check:
            address = w3.to_checksum_address(address)

        full_url = url + address + ".json"
        try:
            abi_json = r.get(full_url).json()
        except:
            raise Exception(f"ABI not found for {address} @ {full_url}.")

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
    @property
    def fragments(self):
        for abi in self.abis:
            for fragment in abi.fragments:
                yield fragment
    
    def get_pgtable_by_name(self, name):

        event = self.get_by_name(name)

        return self.pgtable(event)
    
    def get_by_topic(self, key):

        for event in self.events:
            if (event.topic == key) or (event.topic[:len(key)] == key):
                return event

    def get_by_name(self, key, pos=0):

        for event in self.events:
            print(f"{event.name} != {key}")
            print(event.name == key)
            if (str(event.slug) == key) or (str(event.name) == key):
                print(f"Found {pos}")
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

