import hre from "hardhat";

async function main() {
  const courtAddress = "0xf39Fd6e51aad88F6F4ce6aB8827279cffFb92266";
  
  const EscrowFactory = await hre.ethers.getContractFactory("AgentCourtEscrow");
  const escrow = await EscrowFactory.deploy(courtAddress);

  await escrow.waitForDeployment();

  const contractAddress = await escrow.getAddress();

  console.log(`\n✅ AgentCourtEscrow deployed successfully!`);
  console.log(`Contract Address: ${contractAddress}\n`);
}

main().catch((error) => {
  console.error(error);
  process.exitCode = 1;
});
