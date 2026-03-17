// SPDX-License-Identifier: MIT
pragma solidity ^0.8.19;

import {Test} from "forge-std/Test.sol";

import {OracleCore} from "../src/OracleCore.sol";

contract OracleCoreTest is Test {
    OracleCore internal oracleCore;

    address internal owner = address(this);
    address internal notOwner = address(0xBEEF);

    function setUp() public {
        oracleCore = new OracleCore();
    }

    function test_UpdatePriceStoresLatestData() public {
        vm.warp(1_700_000_000);

        oracleCore.updatePrice("ETH", 314256, 95, 4, 1);

        (uint256 price, uint8 confidence, uint256 timestamp) = oracleCore.getLatestPrice("ETH");
        assertEq(price, 314256);
        assertEq(uint256(confidence), 95);
        assertEq(timestamp, 1_700_000_000);
        assertEq(oracleCore.getHistoryLength("ETH"), 1);
        assertEq(oracleCore.roundCounter(), 1);

        owner; // silence unused warning in strict setups
    }

    function test_RevertWhen_NotOwnerCallsUpdatePrice() public {
        vm.prank(notOwner);
        vm.expectRevert("Ownable: caller is not the owner");
        oracleCore.updatePrice("ETH", 300000, 90, 4, 1);
    }

    function test_HistoryEntryAfterMultipleRounds() public {
        oracleCore.updatePrice("ETH", 300000, 88, 4, 1);
        oracleCore.updatePrice("ETH", 301000, 90, 4, 1);

        (uint256 p0,, uint256 ts0, uint8 u0, uint8 r0, uint256 round0) = oracleCore.getHistoryEntry("ETH", 0);
        (uint256 p1,, uint256 ts1, uint8 u1, uint8 r1, uint256 round1) = oracleCore.getHistoryEntry("ETH", 1);

        assertEq(p0, 300000);
        assertEq(p1, 301000);
        assertEq(u0, 4);
        assertEq(r0, 1);
        assertEq(u1, 4);
        assertEq(r1, 1);
        assertEq(round0, 1);
        assertEq(round1, 2);
        assertGt(ts1, 0);
        assertGt(ts0, 0);
    }

    function testFuzz_UpdatePrice(uint256 rawPrice, uint8 confidence, uint8 nodesUsed, uint8 nodesRejected) public {
        vm.assume(rawPrice > 0 && rawPrice < type(uint128).max);
        vm.assume(confidence <= 100);

        oracleCore.updatePrice("BTC", rawPrice, confidence, nodesUsed, nodesRejected);

        (uint256 storedPrice, uint8 storedConfidence,) = oracleCore.getLatestPrice("BTC");
        assertEq(storedPrice, rawPrice);
        assertEq(storedConfidence, confidence);
    }
}
