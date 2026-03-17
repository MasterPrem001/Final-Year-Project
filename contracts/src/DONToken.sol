// SPDX-License-Identifier: MIT
pragma solidity ^0.8.19;

import {AccessControl} from "@openzeppelin/contracts/access/AccessControl.sol";
import {ERC20} from "@openzeppelin/contracts/token/ERC20/ERC20.sol";

/// @title DONToken
/// @notice AI-DON staking token used by oracle nodes for participation and slashing.
contract DONToken is ERC20, AccessControl {
    bytes32 public constant MINTER_ROLE = keccak256("MINTER_ROLE");
    bytes32 public constant SLASHER_ROLE = keccak256("SLASHER_ROLE");

    uint256 public constant MIN_STAKE = 1000 * 10 ** 18;

    /// @notice Locked stake balance per oracle node.
    mapping(address => uint256) public stakedBalance;

    event Staked(address indexed node, uint256 amount);
    event Unstaked(address indexed node, uint256 amount);
    event Slashed(address indexed node, uint256 amount);

    constructor() ERC20("AI-DON Token", "DON") {
        _grantRole(DEFAULT_ADMIN_ROLE, msg.sender);
        _grantRole(MINTER_ROLE, msg.sender);
        _grantRole(SLASHER_ROLE, msg.sender);
    }

    /// @notice Mint DON to an address (admin/authorized minter only).
    function mint(address to, uint256 amount) external onlyRole(MINTER_ROLE) {
        require(to != address(0), "DONToken: zero address");
        require(amount > 0, "DONToken: amount is zero");
        _mint(to, amount);
    }

    /// @notice Lock DON from caller wallet as oracle participation stake.
    /// @dev The first stake must satisfy minimum node stake requirement.
    function stake(uint256 amount) external {
        require(amount > 0, "DONToken: amount is zero");
        uint256 newStake = stakedBalance[msg.sender] + amount;
        require(newStake >= MIN_STAKE, "DONToken: below minimum stake");

        _transfer(msg.sender, address(this), amount);
        stakedBalance[msg.sender] = newStake;

        emit Staked(msg.sender, amount);
    }

    /// @notice Unlock staked DON back to the caller wallet.
    /// @dev Remaining stake can be zero or still above minimum.
    function unstake(uint256 amount) external {
        require(amount > 0, "DONToken: amount is zero");
        uint256 currentStake = stakedBalance[msg.sender];
        require(currentStake >= amount, "DONToken: insufficient staked balance");

        uint256 remaining = currentStake - amount;
        if (remaining != 0) {
            require(remaining >= MIN_STAKE, "DONToken: remaining below minimum");
        }

        stakedBalance[msg.sender] = remaining;
        _transfer(address(this), msg.sender, amount);

        emit Unstaked(msg.sender, amount);
    }

    /// @notice Slash an oracle node's locked DON tokens.
    /// @dev Slashed tokens are permanently burned from protocol-held stake.
    function slash(address node, uint256 amount) external onlyRole(SLASHER_ROLE) {
        require(node != address(0), "DONToken: zero address");
        require(amount > 0, "DONToken: amount is zero");
        require(stakedBalance[node] >= amount, "DONToken: slash exceeds stake");

        stakedBalance[node] -= amount;
        _burn(address(this), amount);

        emit Slashed(node, amount);
    }

    /// @notice Helper for checking if a node currently satisfies the minimum stake.
    function hasMinimumStake(address node) external view returns (bool) {
        return stakedBalance[node] >= MIN_STAKE;
    }
}
