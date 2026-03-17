// SPDX-License-Identifier: MIT
pragma solidity ^0.8.19;

import {Test} from "forge-std/Test.sol";

import {OracleConsumer} from "../src/OracleConsumer.sol";
import {OracleCore} from "../src/OracleCore.sol";

contract OracleConsumerTest is Test {
    OracleCore internal oracleCore;
    OracleConsumer internal consumer;

    function setUp() public {
        oracleCore = new OracleCore();
        consumer = new OracleConsumer(address(oracleCore));
    }

    function test_GetLatestEthReadsFromOracleCore() public {
        vm.warp(1_700_200_000);
        oracleCore.updatePrice("ETH", 315123, 94, 4, 1);

        (uint256 price, uint8 confidence, uint256 timestamp) = consumer.getLatestEth();

        assertEq(price, 315123);
        assertEq(uint256(confidence), 94);
        assertEq(timestamp, 1_700_200_000);
    }

    function test_GetLatestForAssetReadsCustomAsset() public {
        oracleCore.updatePrice("BTC", 6_250_000, 91, 4, 1);

        (uint256 price, uint8 confidence,) = consumer.getLatestForAsset("BTC");
        assertEq(price, 6_250_000);
        assertEq(uint256(confidence), 91);
    }

    function test_RevertWhen_AssetNotAvailableYet() public {
        vm.expectRevert("OracleCore: no data for asset");
        consumer.getLatestForAsset("SOL");
    }

    function test_RevertWhen_ConstructorGivenZeroAddress() public {
        vm.expectRevert("OracleConsumer: zero oracle address");
        new OracleConsumer(address(0));
    }
}
