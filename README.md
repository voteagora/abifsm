# ABI Fragment Set Manager

A library for working with sets of EVM contracts and their ABIs, mostly for getting consistent naming conventions and working with topics.

Basically syntatic sugar for...
* Iterating over (sorted) events
* Looking up ABI by topic
* Getting the topic from an ABI
* Creating postgres-compatible names that are internally unique against a set of contracts

Plus...

* You can diff ABIs

Also...

* Free software: MIT license
* Documentation: https://abifsm.readthedocs.io.

# Usage

If you want to pull ABIs from the internet, you need a URL where they are hosted. 

`export ABI_URL=https://storage.googleapis.com/$BUCKET/checked/`

...then in your code...

```
    from abifsm import ABI, ABISet

    token = ABI.from_file('token', 'tests/abis/0x54bec61cf9b5daadd12d79196737974243dda684.json')
    gov = ABI.from_internet('gov', '0x7292df10a65793398f77af44da6da1c3cb10932e')
    ptc = ABI.from_internet('ptc', '0xd33bb23fe5fbee2cb78c7d337c3af22c69b5b21a')

    abis = ABISet('mydao', [token, gov, ptc])

    for table_name in abis.pgtables(): # Will be in order of event name + topic to break ties.
        print(table_name)
    
    for table_name in abis.pgtables(sorted=True): # Will be in alphabetical order, including prefixes.
        print(table_name)

    for event in abis.events:
        print(event.topic)
    
    print(abis.pgtable(abis.get_by_name('ProposalCreated', 2)))

    print(abis.pgtable(abis.get_by_topic('ccb45da8')))
```

# Comparing

`abifsm compare 0x1f9840a85d5aF5bf1D1762F925BDADdC4201F984 0xd33bb23fe5fbee2cb78c7d337c3af22c69b5b21`

# Running tests

`pytest`