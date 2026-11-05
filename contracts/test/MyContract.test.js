const { expect } = require("chai");
const { ethers } = require("hardhat");

describe("MyContract", function () {
  it("Should return the initial greeting", async function () {
    const MyContract = await ethers.getContractFactory("MyContract");
    const myContract = await MyContract.deploy("Hello, Hardhat!");
    await myContract.waitForDeployment();

    expect(await myContract.greet()).to.equal("Hello, Hardhat!");
    expect(await myContract.greeting()).to.equal("Hello, Hardhat!");
  });

  it("Should update the greeting", async function () {
    const MyContract = await ethers.getContractFactory("MyContract");
    const myContract = await MyContract.deploy("Hello, Hardhat!");
    await myContract.waitForDeployment();

    await myContract.setGreeting("Hola, Mundo!");
    expect(await myContract.greet()).to.equal("Hola, Mundo!");
  });
});
