// SPDX-License-Identifier: MIT
pragma solidity ^0.8.19;

import {Test} from "forge-std/Test.sol";

import {DONToken} from "../src/DONToken.sol";
import {OracleRegistry} from "../src/OracleRegistry.sol";
import {ReputationEngine} from "../src/ReputationEngine.sol";

contract ReputationEngineTest is Test {
    DONToken internal donToken;
    OracleRegistry internal registry;
    ReputationEngine internal engine;

    address internal node = address(0xA11CE);
    address internal stranger = address(0xBEEF);

    function setUp() public {
        donToken = new DONToken();
        registry = new OracleRegistry();
        engine = new ReputationEngine(address(registry), address(donToken));

        registry.grantRole(registry.REGISTRY_ADMIN_ROLE(), address(engine));
        donToken.grantRole(donToken.SLASHER_ROLE(), address(engine));

        registry.registerNode(node, "AlphaNode");

        donToken.mint(node, 5_000 ether);
        vm.prank(node);
        donToken.stake(2_000 ether);
    }

    function test_ProcessNodeResult_RewardPathNoSlash() public {
        (uint256 newRep, uint256 slashed) = engine.processNodeResult(node, 900, 0);

        (, uint256 storedRep, uint256 totalSubmissions, uint256 flaggedSubmissions,,) = registry.getNode(node);

        // old=700 -> (700*9 + 900)/10 = 720
        assertEq(newRep, 720);
        assertEq(slashed, 0);
        assertEq(storedRep, 720);
        assertEq(totalSubmissions, 1);
        assertEq(flaggedSubmissions, 0);
        assertEq(donToken.stakedBalance(node), 2_000 ether);
    }

    function test_ProcessNodeResult_SlashPath() public {
        (uint256 newRep, uint256 slashed) = engine.processNodeResult(node, 800, 2);

        (, uint256 storedRep, uint256 totalSubmissions, uint256 flaggedSubmissions,,) = registry.getNode(node);

        // 2 anomalies -> 10% slash on 2000 ether => 200 ether
        assertEq(newRep, 710);
        assertEq(storedRep, 710);
        assertEq(slashed, 200 ether);
        assertEq(donToken.stakedBalance(node), 1_800 ether);
        assertEq(totalSubmissions, 1);
        assertEq(flaggedSubmissions, 1);
    }

    function test_RevertWhen_NonEngineAdminCallsProcessNodeResult() public {
        vm.prank(stranger);
        vm.expectRevert();
        engine.processNodeResult(node, 850, 0);
    }

    function testFuzz_ProcessNodeResultSmoothing(uint16 accuracyScore) public {
        vm.assume(accuracyScore <= 1000);

        (uint256 newRep,) = engine.processNodeResult(node, accuracyScore, 0);

        uint256 expected = ((700 * 9) + uint256(accuracyScore)) / 10;
        (, uint256 storedRep,,,,) = registry.getNode(node);

        assertEq(newRep, expected);
        assertEq(storedRep, expected);
    }
}
