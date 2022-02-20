
from scripts.get_weth import get_weth
from scripts.helpful_scripts import get_account
from brownie import config, network, interface
from web3 import Web3


AMOUNT = Web3.toWei(0.05, "ether")
STABLE_INTEREST_MODE = 1
REFERRAL_CODE = 0  # deprecated it is needed for 0 to be passed


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
    converted_latest_prince = Web3.fromWei(latest_price, 'ether')
    print(f"DAI/ETH price is {converted_latest_prince}")
    return float(converted_latest_prince)


def repay_all(amount, lending_pool, account):
    erc20_address = config['networks'][network.show_active()]['dai_token']
    approve_erc20(Web3.toWei(amount, "ether"),
                  lending_pool.address, erc20_address, account)
    # function repay(address asset, uint256 amount, uint256 rateMode, address onBehalfOf)

    repay_tx = lending_pool.repay(
        erc20_address, amount, STABLE_INTEREST_MODE, account.address, {"from": account})
    repay_tx.wait(1)
    print("Repaid")


def main():
    account = get_account()
    erc20_address = config['networks'][network.show_active()]['weth_token']
    if network.show_active() in ["mainnet-fork", "kovan"]:
        get_weth()
    lending_pool = get_lending_pool()
    print(f"lending pool: {lending_pool}")
    # Approve sending out ERC20 tokens
    approve_erc20(AMOUNT, lending_pool.address, erc20_address, account)
    # function deposit(address asset, uint256 amount, address onBehalfOf, uint16 referralCode)
    print('Depositing...')
    tx = lending_pool.deposit(erc20_address, AMOUNT,
                              account.address, REFERRAL_CODE, {"from": account})
    tx.wait(1)
    print("Deposited")
    borrowable_eth, total_dep = get_borrowable_data(lending_pool, account)
    print("Let`s borrow!")
    dai_eth_price_feed = config['networks'][network.show_active(
    )]['dai_eth_price_feed']
    dai_eth_price = get_asset_price(dai_eth_price_feed)
    # we multiply by 0.95 as a buffer, for better health factor
    # borrowable-ETH -> borrowable_dai * 95%
    amount_dai_to_borrow = (1 / dai_eth_price) * (borrowable_eth * 0.95)
    print(f"we are going to borrow {amount_dai_to_borrow} DAI")

    # Now we will borrow
    # function borrow(address asset, uint256 amount, uint256 interestRateMode, uint16 referralCode, address onBehalfOf)
    dai_address = config['networks'][network.show_active()]["dai_token"]
    borrow_tx = lending_pool.borrow(
        dai_address,
        Web3.toWei(amount_dai_to_borrow, "ether"),
        STABLE_INTEREST_MODE,
        REFERRAL_CODE,
        account.address, {"from": account}
    )
    borrow_tx.wait(1)
    print("we borrowed some DAI!")
    get_borrowable_data(lending_pool, account)
    #repay_all(AMOUNT, lending_pool, account)
    print("you just deposited,borrowed,and repayed with AAVE, Brownie,and Chainlink")
