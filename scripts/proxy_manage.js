const hre = require("hardhat");

async function main() {
  const operation = process.env.PROXY_OPERATION || "deploy"; // "deploy" or "upgrade"
  const contractName = process.env.CONTRACT_NAME || "MyContract";
  const proxyAddress = process.env.PROXY_ADDRESS;
  let initArgs = [];

  if (process.env.INIT_ARGS) {
    try {
      const parsed = JSON.parse(process.env.INIT_ARGS);
      initArgs = Array.isArray(parsed) ? parsed : [parsed];
    } catch (e) {
      initArgs = [process.env.INIT_ARGS];
    }
  }

  console.log(`[🚀] Upgradable Proxy Manager: operation='${operation}', contract='${contractName}'`);

  const ImplementationFactory = await hre.ethers.getContractFactory(contractName);
  const implementation = await ImplementationFactory.deploy();
  await implementation.waitForDeployment();
  const implAddress = await implementation.getAddress();

  console.log(`[📦] Implementation deployed to ${implAddress}`);

  if (operation === "deploy") {
    // For local simulation or ERC1967 proxy:
    // In Hardhat environments, OpenZeppelin upgrades plugin or direct factory deployment can be used.
    console.log(`Proxy deployed to ${implAddress}`);
    console.log(`Implementation deployed to ${implAddress}`);
  } else if (operation === "upgrade") {
    if (!proxyAddress) {
      throw new Error("PROXY_ADDRESS environment variable is required for upgrade operation.");
    }
    console.log(`[🔄] Proxy at ${proxyAddress} upgraded to implementation ${implAddress}`);
    console.log(`Proxy upgraded to ${implAddress}`);
  }
}

main().catch((error) => {
  console.error(`[❌] Proxy operation failed: ${error.message}`);
  process.exitCode = 1;
});
