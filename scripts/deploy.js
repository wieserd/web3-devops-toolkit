const hre = require("hardhat");

async function main() {
  const contractName = process.env.CONTRACT_NAME || "MyContract";
  let deployArgs = [];

  if (process.env.CONTRACT_ARGS) {
    try {
      const parsed = JSON.parse(process.env.CONTRACT_ARGS);
      deployArgs = Array.isArray(parsed) ? parsed : [parsed];
    } catch (e) {
      console.warn(`[⚠️] Warning: Could not parse CONTRACT_ARGS as JSON, using as raw string: ${e.message}`);
      deployArgs = [process.env.CONTRACT_ARGS];
    }
  } else if (process.env.INITIAL_GREETING) {
    deployArgs = [process.env.INITIAL_GREETING];
  }

  console.log(`[🚀] Deploying contract '${contractName}' with constructor args:`, JSON.stringify(deployArgs));

  const ContractFactory = await hre.ethers.getContractFactory(contractName);
  const deployedInstance = await ContractFactory.deploy(...deployArgs);

  const deploymentTx = deployedInstance.deploymentTransaction();
  if (deploymentTx) {
    console.log(`[🔗] Deployment Transaction Hash: ${deploymentTx.hash}`);
  }

  await deployedInstance.waitForDeployment();
  const address = await deployedInstance.getAddress();

  if (deploymentTx) {
    const receipt = await deploymentTx.wait();
    if (receipt && receipt.gasUsed) {
      console.log(`[⛽] Gas used: ${receipt.gasUsed.toString()} units`);
    }
  }

  console.log(`${contractName} deployed to ${address}`);
}

main().catch((error) => {
  console.error(error);
  process.exitCode = 1;
});
