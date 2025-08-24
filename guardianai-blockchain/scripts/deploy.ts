import { ethers } from "hardhat";

async function main() {
  console.log("Deploying GuardianLog contract...");

  // Get the contract factory for our GuardianLog contract.
  // A "factory" is an abstraction used to deploy new smart contracts.
  const GuardianLog = await ethers.getContractFactory("GuardianLog");

  // Start the deployment process. This sends a transaction to the blockchain.
  const guardianLog = await GuardianLog.deploy();

  // Wait for the transaction to be mined and the contract to be deployed.
  await guardianLog.waitForDeployment();

  const contractAddress = await guardianLog.getAddress();

  // Log the address of the newly deployed contract to the console.
  // This address is the permanent home of your contract on the Amoy testnet.
  console.log(`✅ GuardianLog contract deployed to: ${contractAddress}`);
}

// We recommend this pattern to be able to use async/await everywhere
// and properly handle errors.
main().catch((error) => {
  console.error(error);
  process.exitCode = 1;
});