// SPDX-License-Identifier: MIT
pragma solidity ^0.8.19;

import {Test} from "forge-std/Test.sol";

import {DONToken} from "../src/DONToken.sol";

contract DONTokenTest is Test {
    DONToken internal token;

    address internal admin = address(this);
    address internal node = address(0xCAFE);
    address internal slasher = address(0xDEAD);

    function setUp() public {
        token = new DONToken();
        token.grantRole(token.SLASHER_ROLE(), slasher);

        token.mint(node, 10_000 ether);
        admin; // silence unused warning in strict setups
    }

    function test_StakeAndUnstakeFlow() public {
        vm.startPrank(node);
        token.stake(2_000 ether);
        assertEq(token.stakedBalance(node), 2_000 ether);

        token.unstake(1_000 ether);
        assertEq(token.stakedBalance(node), 1_000 ether);
        vm.stopPrank();
    }

    function test_RevertWhen_StakeBelowMinimum() public {
        vm.prank(node);
        vm.expectRevert("DONToken: below minimum stake");
        token.stake(999 ether);
    }

    function test_SlashBurnsFromStakedBalance() public {
        vm.prank(node);
        token.stake(2_000 ether);

        uint256 beforeSupply = token.totalSupply();

        vm.prank(slasher);
        token.slash(node, 100 ether);

        assertEq(token.stakedBalance(node), 1_900 ether);
        assertEq(token.totalSupply(), beforeSupply - 100 ether);
    }

    function testFuzz_Stake(uint256 amount) public {
        vm.assume(amount >= token.MIN_STAKE());
        vm.assume(amount <= 10_000 ether);

        address fuzzNode = address(0xB0B);
        token.mint(fuzzNode, amount);

        vm.prank(fuzzNode);
        token.stake(amount);

        assertEq(token.stakedBalance(fuzzNode), amount);
    }
}
