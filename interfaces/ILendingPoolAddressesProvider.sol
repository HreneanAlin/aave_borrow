// SPDX-License-Identifier: MIT

pragma solidity 0.6.6;

interface IlendingPoolAddressesProvider {
    function getLendingPool() external view returns (address);
}
