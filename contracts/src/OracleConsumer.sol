// SPDX-License-Identifier: MIT
pragma solidity ^0.8.19;

interface IOracleCore {
    function getLatestPrice(string calldata asset) external view returns (uint256, uint8, uint256);
}

/// @title OracleConsumer
/// @notice Example consumer contract showing how dApps read AI-DON oracle prices.
contract OracleConsumer {
    IOracleCore public immutable ORACLE_CORE;

    constructor(address oracleCoreAddress) {
        require(oracleCoreAddress != address(0), "OracleConsumer: zero oracle address");
        ORACLE_CORE = IOracleCore(oracleCoreAddress);
    }

    /// @notice Read latest ETH price tuple from OracleCore.
    function getLatestEth() external view returns (uint256 price, uint8 confidence, uint256 timestamp) {
        return ORACLE_CORE.getLatestPrice("ETH");
    }

    /// @notice Generic read helper for any supported asset symbol.
    function getLatestForAsset(string calldata asset)
        external
        view
        returns (uint256 price, uint8 confidence, uint256 timestamp)
    {
        return ORACLE_CORE.getLatestPrice(asset);
    }
}
