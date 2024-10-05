
import argh
from abifsm import ABI, ABISet

def compare(address_1: str, address_2: str):
    print(f"Comparing {address_1} vs {address_2}")

    abi1 = ABI.from_internet('1', address_1)
    abi2 = ABI.from_internet('2', address_2)

    abis1 = ABISet('1', [abi1])
    abis2 = ABISet('2', [abi2])

    print("\n  # SIGNATURES")
    abis1.compare_signatures(abis2)

    print("\n  # EVENTS")
    abis1.compare_events(abis2)

def main():
    parser = argh.ArghParser()
    parser.add_commands([compare])
    parser.dispatch()

if __name__ == "__main__":
    main()