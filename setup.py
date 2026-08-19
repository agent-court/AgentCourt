from setuptools import setup, find_packages

setup(
    name="agentcourt",
    version="0.1.0",
    description="Trust-minimized multi-agent neural dispute arbitration protocol on Base.",
    author="Polybius Labs",
    author_email="contact@polybiuslabs.xyz",
    packages=["agentcourt"],
    package_data={"agentcourt": ["*.json"]},
    include_package_data=True,
    install_requires=[
        "web3>=6.0.0",
        "chromadb>=0.4.0",
        "onnxruntime",
        "openai>=1.0.0",
        "anthropic>=0.18.0",
        "google-generativeai",
        "python-dotenv"
    ],
    python_requires=">=3.10",
)
