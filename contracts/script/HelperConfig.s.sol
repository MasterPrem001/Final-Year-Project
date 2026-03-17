// SPDX-License-Identifier: MIT
pragma solidity ^0.8.19;

import {Script} from "forge-std/Script.sol";

contract HelperConfig is Script {
    struct NetworkConfig {
        string rpcUrl;
        uint256 deployerKey;
        address oracleCore;
        address oracleRegistry;
        address donToken;
        address reputationEngine;
        address oracleConsumer;
    }

    uint256 private constant ANVIL_CHAIN_ID = 31337;
    uint256 private constant SEPOLIA_CHAIN_ID = 11155111;
    uint256 private constant MAINNET_CHAIN_ID = 1;

    // Standard Anvil default account private key for local testing only.
    uint256 private constant DEFAULT_ANVIL_PRIVATE_KEY =
        0xac0974bec39a17e36ba4a6b4d238ff944bacb478cbed5efcae784d7bf4f2ff80;

    NetworkConfig private activeNetworkConfig;

    constructor() {
        activeNetworkConfig = getConfigByChainId(block.chainid);
    }

    function getActiveConfig() external view returns (NetworkConfig memory) {
        return activeNetworkConfig;
    }

    function getConfigByChainId(uint256 chainId) public view returns (NetworkConfig memory) {
        if (chainId == ANVIL_CHAIN_ID) {
            return getAnvilConfig();
        }
        if (chainId == SEPOLIA_CHAIN_ID) {
            return getSepoliaConfig();
        }
        if (chainId == MAINNET_CHAIN_ID) {
            return getMainnetConfig();
        }
        return getAnvilConfig();
    }

    function getAnvilConfig() internal pure returns (NetworkConfig memory) {
        return NetworkConfig({
            rpcUrl: "http://127.0.0.1:8545",
            deployerKey: DEFAULT_ANVIL_PRIVATE_KEY,
            oracleCore: address(0),
            oracleRegistry: address(0),
            donToken: address(0),
            reputationEngine: address(0),
            oracleConsumer: address(0)
        });
    }

    function getSepoliaConfig() internal view returns (NetworkConfig memory) {
        return NetworkConfig({
            rpcUrl: vm.envString("SEPOLIA_RPC_URL"),
            deployerKey: vm.envUint("PRIVATE_KEY"),
            oracleCore: vm.envOr("SEPOLIA_ORACLE_CORE", address(0)),
            oracleRegistry: vm.envOr("SEPOLIA_ORACLE_REGISTRY", address(0)),
            donToken: vm.envOr("SEPOLIA_DON_TOKEN", address(0)),
            reputationEngine: vm.envOr("SEPOLIA_REPUTATION_ENGINE", address(0)),
            oracleConsumer: vm.envOr("SEPOLIA_ORACLE_CONSUMER", address(0))
        });
    }

    function getMainnetConfig() internal view returns (NetworkConfig memory) {
        return NetworkConfig({
            rpcUrl: vm.envString("MAINNET_RPC_URL"),
            deployerKey: vm.envUint("PRIVATE_KEY"),
            oracleCore: vm.envOr("MAINNET_ORACLE_CORE", address(0)),
            oracleRegistry: vm.envOr("MAINNET_ORACLE_REGISTRY", address(0)),
            donToken: vm.envOr("MAINNET_DON_TOKEN", address(0)),
            reputationEngine: vm.envOr("MAINNET_REPUTATION_ENGINE", address(0)),
            oracleConsumer: vm.envOr("MAINNET_ORACLE_CONSUMER", address(0))
        });
    }
}
