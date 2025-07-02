const hre = require("hardhat");

async function main() {
  const initialGreeting = process.env.INITIAL_GREETING || "Hello, Hardhat!";
  const MyContract = await hre.ethers.getContractFactory("MyContract");
  const myContract = await MyContract.deploy(initialGreeting);

  await myContract.waitForDeployment();

  console.log(`MyContract deployed to ${myContract.target}`);
}

main().catch((error) => {
  console.error(error);
  process.exitCode = 1;
});
