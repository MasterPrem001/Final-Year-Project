// SPDX-License-Identifier: MIT
pragma solidity ^0.8.19;

import {AccessControl} from "@openzeppelin/contracts/access/AccessControl.sol";

/// @title OracleRegistry
/// @notice Registry for AI-DON oracle node profiles, status, and on-chain reputation updates.
contract OracleRegistry is AccessControl {
    bytes32 public constant REGISTRY_ADMIN_ROLE = keccak256("REGISTRY_ADMIN_ROLE");

    uint256 public constant STARTING_REPUTATION = 700;
    uint256 public constant MAX_REPUTATION = 1000;

    struct NodeRecord {
        string name;
        uint256 reputation; // 0-1000 score
        uint256 totalSubmissions;
        uint256 flaggedSubmissions;
        bool isActive;
        uint256 registeredAt;
    }

    mapping(address => NodeRecord) private sNodeRecords;
    mapping(address => bool) private sIsRegistered;
    address[] private sNodeAddresses;

    event NodeRegistered(address indexed node, string name, uint256 startingReputation, uint256 registeredAt);
    event NodeDeactivated(address indexed node, uint256 timestamp);
    event ReputationUpdated(
        address indexed node,
        uint256 previousReputation,
        uint256 newReputation,
        uint256 totalSubmissions,
        uint256 flaggedSubmissions
    );

    constructor() {
        _grantRole(DEFAULT_ADMIN_ROLE, msg.sender);
        _grantRole(REGISTRY_ADMIN_ROLE, msg.sender);
    }

    /// @notice Register a new oracle node profile.
    function registerNode(address node, string calldata name) external onlyRole(REGISTRY_ADMIN_ROLE) {
        require(node != address(0), "OracleRegistry: zero address");
        require(!sIsRegistered[node], "OracleRegistry: already registered");
        require(bytes(name).length > 0, "OracleRegistry: name required");

        sNodeRecords[node] = NodeRecord({
            name: name,
            reputation: STARTING_REPUTATION,
            totalSubmissions: 0,
            flaggedSubmissions: 0,
            isActive: true,
            registeredAt: block.timestamp
        });

        sIsRegistered[node] = true;
        sNodeAddresses.push(node);

        emit NodeRegistered(node, name, STARTING_REPUTATION, block.timestamp);
    }

    /// @notice Deactivate an existing node profile.
    function deactivateNode(address node) external onlyRole(REGISTRY_ADMIN_ROLE) {
        require(sIsRegistered[node], "OracleRegistry: node not registered");
        require(sNodeRecords[node].isActive, "OracleRegistry: already inactive");

        sNodeRecords[node].isActive = false;
        emit NodeDeactivated(node, block.timestamp);
    }

    /// @notice Update node reputation and submission counters after an oracle round.
    /// @param node Oracle node wallet address.
    /// @param newReputation New reputation score in [0, 1000].
    /// @param wasFlagged Whether this round's submission was flagged by AI.
    function updateReputation(address node, uint256 newReputation, bool wasFlagged)
        external
        onlyRole(REGISTRY_ADMIN_ROLE)
    {
        require(sIsRegistered[node], "OracleRegistry: node not registered");
        require(newReputation <= MAX_REPUTATION, "OracleRegistry: reputation out of range");

        NodeRecord storage rec = sNodeRecords[node];

        uint256 oldReputation = rec.reputation;
        rec.reputation = newReputation;
        rec.totalSubmissions += 1;
        if (wasFlagged) {
            rec.flaggedSubmissions += 1;
        }

        emit ReputationUpdated(node, oldReputation, rec.reputation, rec.totalSubmissions, rec.flaggedSubmissions);
    }

    /// @notice Return all active node addresses.
    function getActiveNodes() external view returns (address[] memory) {
        uint256 activeCount = 0;
        uint256 i;
        uint256 total = sNodeAddresses.length;

        for (i = 0; i < total; i++) {
            if (sNodeRecords[sNodeAddresses[i]].isActive) {
                activeCount += 1;
            }
        }

        address[] memory active = new address[](activeCount);
        uint256 idx = 0;
        for (i = 0; i < total; i++) {
            address node = sNodeAddresses[i];
            if (sNodeRecords[node].isActive) {
                active[idx] = node;
                idx += 1;
            }
        }

        return active;
    }

    /// @notice Get full node record by address.
    function getNode(address node)
        external
        view
        returns (
            string memory name,
            uint256 reputation,
            uint256 totalSubmissions,
            uint256 flaggedSubmissions,
            bool isActive,
            uint256 registeredAt
        )
    {
        require(sIsRegistered[node], "OracleRegistry: node not registered");

        NodeRecord storage rec = sNodeRecords[node];
        return (rec.name, rec.reputation, rec.totalSubmissions, rec.flaggedSubmissions, rec.isActive, rec.registeredAt);
    }

    /// @notice Helper to check if an address has been registered as an oracle node.
    function isRegistered(address node) external view returns (bool) {
        return sIsRegistered[node];
    }

    /// @notice Return total number of registered nodes.
    function getRegisteredNodeCount() external view returns (uint256) {
        return sNodeAddresses.length;
    }
}
