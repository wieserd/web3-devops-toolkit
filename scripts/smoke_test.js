const hre = require("hardhat");

async function main() {
  const contractName = process.env.CONTRACT_NAME;
  const address = process.env.CONTRACT_ADDRESS;
  const callsStr = process.env.SMOKE_CALLS || "[]";

  if (!contractName || !address) {
    throw new Error("CONTRACT_NAME and CONTRACT_ADDRESS environment variables are required.");
  }

  let calls = [];
  try {
    calls = JSON.parse(callsStr);
  } catch (e) {
    throw new Error(`Failed to parse SMOKE_CALLS as JSON: ${e.message}`);
  }

  console.log(`[🧪] Connecting to ${contractName} at ${address}...`);
  const contract = await hre.ethers.getContractAt(contractName, address);

  for (let i = 0; i < calls.length; i++) {
    const { method, args = [], expected } = calls[i];
    if (!method) {
      throw new Error(`Call #${i + 1} is missing required 'method' property`);
    }

    if (typeof contract[method] !== "function") {
      throw new Error(`Contract '${contractName}' has no method named '${method}'`);
    }

    console.log(`  [🔍] Executing: ${contractName}.${method}(${JSON.stringify(args).slice(1, -1)})...`);
    const result = await contract[method](...args);
    const resultStr = result !== null && result !== undefined ? result.toString() : "";
    console.log(`  [📌] Return value: ${resultStr}`);

    if (expected !== undefined && expected !== null) {
      const expectedStr = expected.toString();
      if (resultStr !== expectedStr) {
        throw new Error(
          `Assertion failed on ${contractName}.${method}(): expected '${expectedStr}', but received '${resultStr}'`
        );
      }
      console.log(`  [✅] Assertion passed: ${method}() == '${expectedStr}'`);
    }
  }

  console.log(`[🎉] All on-chain smoke tests passed for ${contractName} at ${address}`);
}

main().catch((error) => {
  console.error(`[❌] Smoke test failed: ${error.message}`);
  process.exitCode = 1;
});
