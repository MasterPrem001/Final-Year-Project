// SPDX-License-Identifier: MIT
pragma solidity ^0.8.19;

import {Test} from "forge-std/Test.sol";

import {OracleRegistry} from "../src/OracleRegistry.sol";

contract OracleRegistryTest is Test {
    OracleRegistry internal registry;

    address internal admin = address(this);
    address internal outsider = address(0xABCD);
    address internal node1 = address(0x1111);
    address internal node2 = address(0x2222);

    function setUp() public {
        registry = new OracleRegistry();
        admin; // silence unused warning in strict setups
    }

    function test_RegisterNodeSetsDefaultState() public {
        vm.warp(1_700_100_000);
        registry.registerNode(node1, "AlphaNode");

        (
            string memory name,
            uint256 reputation,
            uint256 totalSubmissions,
            uint256 flaggedSubmissions,
            bool isActive,
            uint256 registeredAt
        ) = registry.getNode(node1);

        assertEq(name, "AlphaNode");
        assertEq(reputation, 700);
        assertEq(totalSubmissions, 0);
        assertEq(flaggedSubmissions, 0);
        assertTrue(isActive);
        assertEq(registeredAt, 1_700_100_000);
    }

    function test_RevertWhen_NonAdminRegistersNode() public {
        vm.prank(outsider);
        vm.expectRevert();
        registry.registerNode(node1, "AlphaNode");
    }

    function test_UpdateReputationIncrementsCounters() public {
        registry.registerNode(node1, "AlphaNode");

        registry.updateReputation(node1, 810, true);

        (, uint256 rep, uint256 totalSubmissions, uint256 flaggedSubmissions,,) = registry.getNode(node1);
        assertEq(rep, 810);
        assertEq(totalSubmissions, 1);
        assertEq(flaggedSubmissions, 1);
    }

    function test_GetActiveNodesFiltersDeactivatedNodes() public {
        registry.registerNode(node1, "AlphaNode");
        registry.registerNode(node2, "BetaNode");

        registry.deactivateNode(node2);

        address[] memory active = registry.getActiveNodes();
        assertEq(active.length, 1);
        assertEq(active[0], node1);
    }

    function testFuzz_UpdateReputation(uint16 score, bool wasFlagged) public {
        vm.assume(score <= 1000);

        address fuzzNode = address(0x3333);
        registry.registerNode(fuzzNode, "FuzzNode");
        registry.updateReputation(fuzzNode, score, wasFlagged);

        (, uint256 reputation, uint256 totalSubmissions, uint256 flaggedSubmissions,,) = registry.getNode(fuzzNode);
        assertEq(reputation, score);
        assertEq(totalSubmissions, 1);
        assertEq(flaggedSubmissions, wasFlagged ? 1 : 0);
    }
}
