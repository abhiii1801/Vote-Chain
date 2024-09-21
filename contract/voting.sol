// SPDX-License-Identifier: MIT
pragma solidity ^0.8.0;

contract Voting {
    struct Party {
        string name;
        uint voteCount;
    }

    address public admin;
    Party[] public parties;
    mapping(address => bool) public hasVoted;
    bool public votingStarted;

    modifier onlyAdmin() {
        require(msg.sender == admin, "Only admin can call this");
        _;
    }

    modifier votingActive() {
        require(votingStarted, "Voting is not started");
        _;
    }

    constructor() {
        admin = msg.sender;
        votingStarted = false;
    }

    function addParty(string memory _name) public onlyAdmin {

        for (uint i = 0; i < parties.length; i++) {
            require(keccak256(bytes(parties[i].name)) != keccak256(bytes(_name)), "Party with this name already exists");
        }
        parties.push(Party(_name, 0));
    }

    function toggleVoting() public onlyAdmin returns (bool) {
        votingStarted = !votingStarted;
        return votingStarted;
    }

    function vote(uint _partyIndex) public votingActive {
        // require(!hasVoted[msg.sender], "You have already voted");
        require(_partyIndex < parties.length, "Invalid party index");

        hasVoted[msg.sender] = true;
        parties[_partyIndex].voteCount++;
    }

    function getResults() public view returns (Party[] memory) {
        return parties;
    }

    function getPartyNames() public view returns (string[] memory) {
        string[] memory names = new string[](parties.length);
        for (uint i = 0; i < parties.length; i++) {
            names[i] = parties[i].name;
        }
        return names;
    }

}