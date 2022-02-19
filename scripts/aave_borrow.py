
from scripts.get_weth import get_weth
from scripts.helpful_scripts import get_account
from brownie import config, network, interface
from web3 import Web3


AMOUNT = Web3.toWei(0.05, "ether")


def get_lending_pool():
    lending_pool_addresses_provider = interface.IlendingPoolAddressesProvider(
        config["networks"][network.show_active()]["lending_pool_addresses_provider"])
    lending_pool_address = lending_pool_addresses_provider.getLendingPool()
    lending_pool = interface.ILendingPool(lending_pool_address)
    return lending_pool


def approve_erc20(amount, spender, erc20_address, account):
    # API
    # Address
    print("approving ERC20 toke...")
    erc20 = interface.IERC20(erc20_address)
    tx = erc20.approve(spender, amount, {"from": account})
    tx.wait(1)
    print("Approved")
    return tx


def get_borrowable_data(lending_pool, account):
    (total_collateral_eth,
     total_dept_eth,
     available_borrow_eth,
     current_liquidation_threshold,
     ltv,
     health_factor) = lending_pool.getUserAccountData(account.address)
    available_borrow_eth = Web3.fromWei(available_borrow_eth, "ether")
    total_collateral_eth = Web3.fromWei(total_collateral_eth, "ether")
    total_dept_eth = Web3.fromWei(total_dept_eth, "ether")
    print(f"You have {total_collateral_eth} worth of ETH deposited")
    print(f"You have {total_dept_eth} worth of ETH borrowed")
    print(f"You can borrow {available_borrow_eth} worth of ETH ")
    return (float(available_borrow_eth), float(total_dept_eth))


def get_asset_price(price_feed_address):
    # ABI
    # Address
    dai_eth_price_feed = interface.IAggregatorV3(price_feed_address)
    latest_price = dai_eth_price_feed.latestRoundData()[
        1]  # prince is at index 1
    print(f"DAI/ETH price is {latest_price}")
    return float(latest_price)


def main():
    account = get_account()
    erc20_address = config['networks'][network.show_active()]['weth_token']
    if network.show_active() in ["mainnet-fork"]:
        get_weth()
    lending_pool = get_lending_pool()
    print(f"lending pool: {lending_pool}")
    # Approve sending out ERC20 tokens
    approve_erc20(AMOUNT, lending_pool.address, erc20_address, account)
    # function deposit(address asset, uint256 amount, address onBehalfOf, uint16 referralCode)
    print('Depositing...')
    tx = lending_pool.deposit(erc20_address, AMOUNT,
                              account.address, 0, {"from": account})
    tx.wait(1)
    print("Deposited")
    borrowable_eth, total_dep = get_borrowable_data(lending_pool, account)
    print("Let`s borrow!")
    dai_eth_price_feed = config['networks'][network.show_active(
    )]['dai_eth_price_feed']
    dai_eth_price = get_asset_price(dai_eth_price_feed)
