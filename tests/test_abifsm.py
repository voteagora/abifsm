#!/usr/bin/env python

"""Tests for `abifsm` package."""
import pytest, os

from abifsm import ABI, ABISet, FQPGSqlGen

def skip_if_env_not_set(env_var):
    return pytest.mark.skipif(
        env_var not in os.environ,
        reason=f"Environment variable '{env_var}' is not set"
    )

skip_if_no_abi_url = skip_if_env_not_set("ABI_URL")

@pytest.fixture
def abiset():
    abi1 = ABI.from_file('token', 'tests/abis/0x54bec61cf9b5daadd12d79196737974243dda684.json')
    abi2 = ABI.from_file('gov', 'tests/abis/0x7292df10a65793398f77af44da6da1c3cb10932e.json')
    abi3 = ABI.from_file('ptc', 'tests/abis/0xd33bb23fe5fbee2cb78c7d337c3af22c69b5b21a.json')

    abis = ABISet('mydao', [abi1, abi2, abi3])
    return abis

def test_event_iteration(abiset):

    count = 0
    for event in abiset.events:
        count += 1
        print(event.name, abiset.pgtable(event), event.topic)
    
    assert count == 30

def test_abi_len():

    abi = ABI.from_file('token', 'tests/abis/0x54bec61cf9b5daadd12d79196737974243dda684.json')

    assert len(abi) == 71

def test_abis_len(abiset):

    assert len(abiset) == 162

def test_compare_tables_matching(abiset):

    abiset.compare_tables(abiset)
    diff = abiset.compare_tables(abiset, printit=False)

    diffs = list(diff)
    assert len(diffs) == 30 # there should be 30 things compared.
    assert len([d for d in diffs if d[:2].strip() != '']) == 0 # there should be no mismatches.

def test_compare_signatures_matching(abiset):

    abiset.compare_signatures(abiset)
    diff = abiset.compare_signatures(abiset, printit=False)

    diffs = list(diff)
    assert len(diffs) == 162 # there should be 30 things compared.
    assert len([d for d in diffs if d[:2].strip() != '']) == 0 # there should be no mismatches.

def test_compare_signatures_mismatching():

    token_1_abi = ABI.from_file('token', 'tests/abis/0xC18360217D8F7Ab5e7c516566761Ea12Ce7F9D72.json')
    token_2_abi = ABI.from_file('token', 'tests/abis/0x1f9840a85d5aF5bf1D1762F925BDADdC4201F984.json')

    abis1 = ABISet('1', [token_1_abi])
    abis2 = ABISet('2', [token_2_abi])

    abis1.compare_signatures(abis2)
    diff = abis1.compare_signatures(abis2, printit=False)

    diffs = list(diff)
    assert len(diffs) == 43 # there should be 43 things compared.
    assert len([d for d in diffs if d[:2].strip() != '']) == 32 # there should be 32 differences.

def test_compare_events_mismatching():

    token_1_abi = ABI.from_file('token', 'tests/abis/0xC18360217D8F7Ab5e7c516566761Ea12Ce7F9D72.json')
    token_2_abi = ABI.from_file('token', 'tests/abis/0x1f9840a85d5aF5bf1D1762F925BDADdC4201F984.json')

    abis1 = ABISet('1', [token_1_abi])
    abis2 = ABISet('2', [token_2_abi])

    abis1.compare_events(abis2)
    diff = abis1.compare_events(abis2, printit=False)

    diffs = list(diff)
    assert len(diffs) == 7 # there should be 7 things compared.
    assert len([d for d in diffs if d[:2].strip() != '']) == 5 # there should be 32 differences.

@skip_if_no_abi_url
def test_read_from_internet():

    abi_b = ABI.from_file('token', 'tests/abis/0x54bec61cf9b5daadd12d79196737974243dda684.json')
    abi_n = ABI.from_internet('token', '0x54bec61cf9b5daadd12d79196737974243dda684')

def test_lookup_and_table_naming(abiset):

    assert abiset.get_by_topic('ccb45da8').name == 'ProposalThresholdSet'
    assert abiset.get_by_topic('ccb45da8d5717e6c4544694297c4ba5cf151d455c9bb0ed4fc7a38411bc05461').slug == 'proposal_threshold_set'
    assert abiset.pgtable(abiset.get_by_topic('ccb45da8d5717e6c4544694297c4ba5cf151d455c9bb0ed4fc7a38411bc05461')) == 'mydao_gov_proposal_threshold_set'
    assert abiset.get_by_name('proposal_created', 2).topic == 'c8df7ff219f3c0358e14500814d8b62b443a4bebf3a596baa60b9295b1cf1bde'
    assert abiset.get_by_name('ProposalCreated', 2).topic == 'c8df7ff219f3c0358e14500814d8b62b443a4bebf3a596baa60b9295b1cf1bde'
    assert abiset.get_by_signature('ProposalCreated(uint256,address,address[],uint256[],string[],bytes[],uint256,uint256,string,uint8)').topic == 'c8df7ff219f3c0358e14500814d8b62b443a4bebf3a596baa60b9295b1cf1bde'

def test_table_name_gen(abiset):

    pg = FQPGSqlGen(abiset)

    assert pg['ccb45da8'] == 'mydao_gov_proposal_threshold_set'

def test_fully_qualified_table_name_gen(abiset):

    pg = FQPGSqlGen(abiset, 'indexer')

    obj = pg['ProposalThresholdSet']

    assert obj == 'indexer.mydao_gov_proposal_threshold_set'

@skip_if_no_abi_url
def test_snippet_in_readme():

    token = ABI.from_file('token', 'tests/abis/0x54bec61cf9b5daadd12d79196737974243dda684.json')
    gov = ABI.from_internet('gov', '0x7292df10a65793398f77af44da6da1c3cb10932e')
    ptc = ABI.from_internet('ptc', '0xd33bb23fe5fbee2cb78c7d337c3af22c69b5b21a')

    abis = ABISet('mydao', [token, gov, ptc])

    for table_name in abis.pgtables(): # Will be in order of event name + topic to break ties.
        print(table_name)
    
    for table_name in abis.pgtables(sort=True): # Will be in alphabetical order, including prefixes.
        print(table_name)
    
    for event in abis.events:
        print(event.topic)
    
    print(abis.pgtable(abis.get_by_name('ProposalCreated', 2)))

    print(abis.pgtable(abis.get_by_topic('ccb45da8')))
