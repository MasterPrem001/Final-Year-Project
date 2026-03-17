// SPDX-License-Identifier: MIT
pragma solidity ^0.8.19;

import {Ownable} from "@openzeppelin/contracts/access/Ownable.sol";

/// @title OracleCore
/// @notice Core AI-DON oracle contract that stores consensus prices and on-chain history per asset.
contract OracleCore is Ownable {
    struct DataPoint {
        uint256 price; // Price scaled by 100 (e.g., 3142.56 USD => 314256)
        uint8 confidence; // 0-100 confidence score from AI pipeline
        uint256 timestamp; // block.timestamp at update time
        uint8 nodesUsed; // Number of accepted oracle nodes
        uint8 nodesRejected; // Number of rejected/flagged oracle nodes
        uint256 roundId; // Global AI-DON round identifier
    }

    /// @dev Full on-chain history for each asset symbol (ETH, BTC, SOL, etc.).
    mapping(string => DataPoint[]) private sPriceHistory;

    /// @notice Global round counter incremented on each update call.
    uint256 public roundCounter;

    event PriceUpdated(
        string indexed asset,
        uint256 price,
        uint8 confidence,
        uint8 nodesUsed,
        uint8 nodesRejected,
        uint256 timestamp,
        uint256 roundId
    );

    constructor() {}

    /// @notice Store a new AI consensus datapoint for an asset.
    /// @dev Only backend owner wallet may write oracle updates.
    function updatePrice(string calldata asset, uint256 price, uint8 confidence, uint8 nodesUsed, uint8 nodesRejected)
        external
        onlyOwner
    {
        require(bytes(asset).length > 0, "OracleCore: asset required");
        require(price > 0, "OracleCore: invalid price");
        require(confidence <= 100, "OracleCore: confidence > 100");

        roundCounter += 1;

        DataPoint memory point = DataPoint({
            price: price,
            confidence: confidence,
            timestamp: block.timestamp,
            nodesUsed: nodesUsed,
            nodesRejected: nodesRejected,
            roundId: roundCounter
        });

        sPriceHistory[asset].push(point);

        emit PriceUpdated(
            asset, point.price, point.confidence, point.nodesUsed, point.nodesRejected, point.timestamp, point.roundId
        );
    }

    /// @notice Returns latest datapoint summary expected by consumer contracts.
    function getLatestPrice(string calldata asset)
        external
        view
        returns (uint256 price, uint8 confidence, uint256 timestamp)
    {
        uint256 len = sPriceHistory[asset].length;
        require(len > 0, "OracleCore: no data for asset");

        DataPoint storage latest = sPriceHistory[asset][len - 1];
        return (latest.price, latest.confidence, latest.timestamp);
    }

    /// @notice Returns history length for an asset.
    function getHistoryLength(string calldata asset) external view returns (uint256) {
        return sPriceHistory[asset].length;
    }

    /// @notice Returns a historical datapoint by index for an asset.
    function getHistoryEntry(string calldata asset, uint256 index)
        external
        view
        returns (
            uint256 price,
            uint8 confidence,
            uint256 timestamp,
            uint8 nodesUsed,
            uint8 nodesRejected,
            uint256 roundId
        )
    {
        require(index < sPriceHistory[asset].length, "OracleCore: history index out of bounds");

        DataPoint storage point = sPriceHistory[asset][index];
        return (point.price, point.confidence, point.timestamp, point.nodesUsed, point.nodesRejected, point.roundId);
    }
}
