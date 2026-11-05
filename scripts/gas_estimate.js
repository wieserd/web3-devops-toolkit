const hre = require("hardhat");

async function main() {
  const contractName = process.env.CONTRACT_NAME || "MyContract";
  let deployArgs = [];

  if (process.env.CONTRACT_ARGS) {
    try {
      const parsed = JSON.parse(process.env.CONTRACT_ARGS);
      deployArgs = Array.isArray(parsed) ? parsed : [parsed];
    } catch (e) {
      deployArgs = [process.env.CONTRACT_ARGS];
    }
  } else if (process.env.INITIAL_GREETING) {
    deployArgs = [process.env.INITIAL_GREETING];
  }

  console.log(`[🔍] Estimating deployment gas for '${contractName}'...`);
  const ContractFactory = await hre.ethers.getContractFactory(contractName);
  const deployTx = await ContractFactory.getDeployTransaction(...deployArgs);

  const estimatedGas = await hre.ethers.provider.estimateGas(deployTx);
  const feeData = await hre.ethers.provider.getFeeData();
  const gasPrice = feeData.gasPrice || 0n;
  const estimatedCostWei = estimatedGas * gasPrice;

  console.log(`[⛽] Estimated Gas Units: ${estimatedGas.toString()}`);
  console.log(`[⛽] Gas Price (Wei): ${gasPrice.toString()}`);
  console.log(`[⛽] Estimated Cost (Wei): ${estimatedCostWei.toString()}`);
}

main().catch((error) => {
  console.error(`[❌] Gas estimation failed: ${error.message}`);
  process.exitCode = 1;
});
