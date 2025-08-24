// SPDX-License-Identifier: MIT
pragma solidity ^0.8.9;

// This is our main smart contract.
contract GuardianLog {

    // This is a custom data structure to hold the details of an evidence log.
    struct Evidence {
        uint256 id;
        uint256 timestamp;
        string evidenceHash;
        string gpsCoordinates;
        address loggedBy; // The address that logged this event (our API server).
    }

    // A counter to give each new log a unique ID.
    uint256 private logCounter;

    // A mapping is like a dictionary or hash map. It links a log ID (a number) 
    // to its corresponding Evidence struct.
    mapping(uint256 => Evidence) public evidenceLogs;

    // An "event" is like a broadcast or a log message. When we log evidence,
    // the contract will emit this event, which can be easily tracked.
    event EvidenceLogged(uint256 id, uint256 timestamp, string evidenceHash);

    /**
     * @dev Public function to log a new piece of evidence.
     * This is the function our Core API will call.
     * "_evidenceHash" is the SHA-256 hash of the evidence file.
     * "_timestamp" is the time the event occurred.
     * "_gpsCoordinates" are the location coordinates.
     */
    function logEvidence(
        string memory _evidenceHash, 
        uint256 _timestamp, 
        string memory _gpsCoordinates
    ) public {
        // Increment the counter to get a new unique ID.
        logCounter++;

        // Create a new Evidence struct in memory and store it in our mapping.
        evidenceLogs[logCounter] = Evidence(
            logCounter,
            _timestamp,
            _evidenceHash,
            _gpsCoordinates,
            msg.sender // msg.sender is a built-in variable for the address that called the function.
        );

        // Emit the event to the blockchain.
        emit EvidenceLogged(logCounter, _timestamp, _evidenceHash);
    }
}