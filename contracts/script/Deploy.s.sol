// SPDX-License-Identifier: MIT
pragma solidity ^0.8.19;

import {Script} from "forge-std/Script.sol";

import {DONToken} from "../src/DONToken.sol";
import {OracleConsumer} from "../src/OracleConsumer.sol";
import {OracleCore} from "../src/OracleCore.sol";
import {OracleRegistry} from "../src/OracleRegistry.sol";
import {ReputationEngine} from "../src/ReputationEngine.sol";

contract Deploy is Script {
    struct DeploymentAddresses {
        address oracleCore;
        address oracleRegistry;
        address donToken;
        address reputationEngine;
        address oracleConsumer;
    }

    function run() external returns (DeploymentAddresses memory deployed) {
        vm.startBroadcast();

        OracleCore oracleCore = new OracleCore();
        OracleRegistry oracleRegistry = new OracleRegistry();
        DONToken donToken = new DONToken();
        ReputationEngine reputationEngine = new ReputationEngine(address(oracleRegistry), address(donToken));
        OracleConsumer oracleConsumer = new OracleConsumer(address(oracleCore));

        vm.stopBroadcast();

        deployed = DeploymentAddresses({
            oracleCore: address(oracleCore),
            oracleRegistry: address(oracleRegistry),
            donToken: address(donToken),
            reputationEngine: address(reputationEngine),
            oracleConsumer: address(oracleConsumer)
        });

        return deployed;
    }
}
