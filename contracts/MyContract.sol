// SPDX-License-Identifier: MIT
pragma solidity ^0.8.20;

contract MyContract {
    string public greeting;

    constructor(string memory _greeting) {
        greeting = _greeting;
    }

    function setGreeting(string memory _newGreeting) public {
        greeting = _newGreeting;
    }
}
