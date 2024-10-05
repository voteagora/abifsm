#!/usr/bin/env python

"""Tests for `abifsm` package."""

import pytest


from abifsm import ABI, ABISet

@pytest.fixture
def abiset():
    abi1 = ABI.from_file('token', 'tests/abis/0x54bec61cf9b5daadd12d79196737974243dda684.json')
    abi2 = ABI.from_file('gov', 'tests/abis/0x7292df10a65793398f77af44da6da1c3cb10932e.json')
    abi3 = ABI.from_file('ptc', 'tests/abis/0xd33bb23fe5fbee2cb78c7d337c3af22c69b5b21a.json')

    abis = ABISet('testnftdao', [abi1, abi2, abi3])
    return abis

def test_event_iteration(abiset):

    count = 0
    for event in abiset.events:
        count += 1
        print(event.name, abiset.pgtable(event), event.topic)
    
    assert count == 30

def test_read_from_internet():

    abi_b = ABI.from_file('token', 'tests/abis/0x54bec61cf9b5daadd12d79196737974243dda684.json')
    abi_n = ABI.from_internet('token', '0x54bec61cf9b5daadd12d79196737974243dda684')

def test_lookup_and_table_naming(abiset):

    assert abiset.get_by_topic('ccb45da8').name == 'ProposalThresholdSet'
    assert abiset.get_by_topic('ccb45da8d5717e6c4544694297c4ba5cf151d455c9bb0ed4fc7a38411bc05461').slug == 'proposal_threshold_set'
    assert abiset.pgtable(abiset.get_by_topic('ccb45da8d5717e6c4544694297c4ba5cf151d455c9bb0ed4fc7a38411bc05461')) == 'testnftdao_gov_proposal_threshold_set'
    assert abiset.get_by_name('proposal_created', 2).topic == 'c8df7ff219f3c0358e14500814d8b62b443a4bebf3a596baa60b9295b1cf1bde'
    assert abiset.get_by_name('ProposalCreated', 2).topic == 'c8df7ff219f3c0358e14500814d8b62b443a4bebf3a596baa60b9295b1cf1bde'
