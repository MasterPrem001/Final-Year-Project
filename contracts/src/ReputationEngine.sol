// SPDX-License-Identifier: MIT
pragma solidity ^0.8.19;

import {AccessControl} from "@openzeppelin/contracts/access/AccessControl.sol";

import {DONToken} from "./DONToken.sol";
import {OracleRegistry} from "./OracleRegistry.sol";

/// @title ReputationEngine
/// @notice Applies AI-DON on-chain reputation smoothing and anomaly-based stake slashing.
contract ReputationEngine is AccessControl {
    bytes32 public constant ENGINE_ADMIN_ROLE = keccak256("ENGINE_ADMIN_ROLE");

    uint256 public constant MAX_REPUTATION = 1000;
    uint256 public constant SLASH_BPS_PER_ANOMALY = 500; // 5.00% in basis points.
    uint256 public constant BPS_DENOMINATOR = 10_000;

    OracleRegistry public immutable REGISTRY;
    DONToken public immutable DON_TOKEN;

    event ReputationSlashed(
        address indexed node,
        uint256 previousReputation,
        uint256 newReputation,
        uint256 slashedAmount,
        uint256 anomalyCount
    );

    event ReputationRewarded(
        address indexed node, uint256 previousReputation, uint256 newReputation, uint256 accuracyScore
    );

    constructor(address registryAddress, address donTokenAddress) {
        require(registryAddress != address(0), "ReputationEngine: zero registry");
        require(donTokenAddress != address(0), "ReputationEngine: zero token");

        REGISTRY = OracleRegistry(registryAddress);
        DON_TOKEN = DONToken(donTokenAddress);

        _grantRole(DEFAULT_ADMIN_ROLE, msg.sender);
        _grantRole(ENGINE_ADMIN_ROLE, msg.sender);
    }

    /// @notice Process one node's oracle result and update both reputation + stake.
    /// @dev This contract must be granted REGISTRY_ADMIN_ROLE in OracleRegistry and
    ///      SLASHER_ROLE in DONToken before this function can execute end-to-end.
    /// @param node Oracle node address.
    /// @param accuracyScore AI-computed accuracy score in [0, 1000].
    /// @param anomalyCount Number of anomalies attributed to this node in the round.
    function processNodeResult(address node, uint256 accuracyScore, uint256 anomalyCount)
        external
        onlyRole(ENGINE_ADMIN_ROLE)
        returns (uint256 newReputation, uint256 slashedAmount)
    {
        require(node != address(0), "ReputationEngine: zero node");
        require(accuracyScore <= MAX_REPUTATION, "ReputationEngine: accuracy out of range");

        (, uint256 oldReputation,,,,) = REGISTRY.getNode(node);

        // Integer exponential smoothing:
        // new_score = (old_score * 9 + accuracy_score) / 10
        newReputation = ((oldReputation * 9) + accuracyScore) / 10;
        if (newReputation > MAX_REPUTATION) {
            newReputation = MAX_REPUTATION;
        }

        bool wasFlagged = anomalyCount > 0;

        // 5% slash per anomaly detected, applied to current staked balance.
        if (wasFlagged) {
            uint256 stake = DON_TOKEN.stakedBalance(node);
            uint256 slashBps = anomalyCount * SLASH_BPS_PER_ANOMALY;
            if (slashBps > BPS_DENOMINATOR) {
                slashBps = BPS_DENOMINATOR; // Cap at 100% of current stake.
            }

            slashedAmount = (stake * slashBps) / BPS_DENOMINATOR;
            if (slashedAmount > 0) {
                DON_TOKEN.slash(node, slashedAmount);
            }
        }

        REGISTRY.updateReputation(node, newReputation, wasFlagged);

        if (wasFlagged) {
            emit ReputationSlashed(node, oldReputation, newReputation, slashedAmount, anomalyCount);
        } else {
            emit ReputationRewarded(node, oldReputation, newReputation, accuracyScore);
        }
    }
}
