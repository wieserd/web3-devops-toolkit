const fs = require("fs");
const path = require("path");
require("@nomicfoundation/hardhat-toolbox");

function loadNetworks() {
  const networksConfigPath = path.resolve(__dirname, "../config/networks.json");
  const networks = {
    localhost: {
      url: "http://127.0.0.1:8545",
    },
  };

  if (fs.existsSync(networksConfigPath)) {
    try {
      const data = JSON.parse(fs.readFileSync(networksConfigPath, "utf-8"));
      for (const [netName, netConfig] of Object.entries(data)) {
        if (netName === "localhost" || netName === "hardhat") continue;

        const envRpcKey = `${netName.toUpperCase().replace(/[^A-Z0-9]/g, "_")}_RPC_URL`;
        const rpcUrl = process.env[envRpcKey] || netConfig.rpc_url || "";
        const accounts = process.env.PRIVATE_KEY ? [process.env.PRIVATE_KEY] : [];

        networks[netName] = {
          url: rpcUrl,
          chainId: netConfig.chain_id,
          accounts: accounts,
        };
      }
    } catch (e) {
      console.warn(`[⚠️] Warning: Could not load networks.json: ${e.message}`);
    }
  }

  return networks;
}

/** @type import('hardhat/config').HardhatUserConfig */
module.exports = {
  solidity: "0.8.20",
  paths: {
    sources: "./",
    artifacts: "../artifacts",
    cache: "../cache"
  },
  networks: loadNetworks(),
  etherscan: {
    apiKey: process.env.ETHERSCAN_API_KEY,
  },
};
