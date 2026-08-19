from setuptools import setup, find_packages

setup(
    name="agentcourt",
    version="3.0.0",
    description="Decentralized multi-LLM escrow and proportional arbitration protocol on Base",
    author="AgentCourt Protocol",
    packages=find_packages(),
    install_requires=[
        "web3>=7.0.0",
        "chromadb>=1.5.0",
    ],
    python_requires=">=3.10",
)
