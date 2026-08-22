// SPDX-License-Identifier: MIT
pragma solidity ^0.8.20;

/**
 * @title AgentEscrowV4
 * @notice ERC-8183 Compliant Agentic Commerce Escrow with Multi-Agent Court Evaluation.
 */
contract AgentEscrowV4 {
    enum JobStatus { Open, Funded, Submitted, Terminal }

    struct Job {
        uint256 jobId;
        address client;
        address provider;
        address evaluator;      // AgentCourt Juror Gateway / Deliberation Daemon
        uint256 budget;
        uint256 expiry;
        bytes32 taskHash;       // Offchain spec hash (IPFS/JSON)
        bytes32 deliverableHash;// Provider submission hash
        JobStatus status;
        uint256 workerSplitBps; // 0 to 10000 (Basis Points)
        bool exists;
    }

    address public owner;
    address public courtGateway; // The authorized AgentCourt multi-juror consensus executor
    uint256 public jobCount;

    mapping(uint256 => Job) public jobs;

    event JobCreated(uint256 indexed jobId, address indexed client, address indexed provider, address evaluator, uint256 budget, uint256 expiry);
    event JobFunded(uint256 indexed jobId, uint256 amount);
    event JobSubmitted(uint256 indexed jobId, bytes32 deliverableHash);
    event JobEvaluated(uint256 indexed jobId, uint256 workerSplitBps, string courtRuling);
    event JobRefunded(uint256 indexed jobId, string reason);

    modifier onlyOwner() {
        require(msg.sender == owner, "Only protocol owner");
        _;
    }

    modifier onlyCourt() {
        require(msg.sender == courtGateway, "Only authorized AgentCourt executor");
        _;
    }

    constructor(address _courtGateway) {
        owner = msg.sender;
        courtGateway = _courtGateway;
    }

    function setCourtGateway(address _newGateway) external onlyOwner {
        require(_newGateway != address(0), "Invalid gateway address");
        courtGateway = _newGateway;
    }

    /**
     * @notice ERC-8183: Step 1 - Client creates a job specification
     */
    function createJob(
        address _provider,
        address _evaluator,
        uint256 _expiry,
        bytes32 _taskHash
    ) external returns (uint256) {
        require(_provider != address(0), "Invalid provider address");
        require(_expiry > block.timestamp, "Expiry must be in future");

        jobCount++;
        uint256 newJobId = jobCount;

        address designatedEvaluator = (_evaluator == address(0)) ? courtGateway : _evaluator;

        jobs[newJobId] = Job({
            jobId: newJobId,
            client: msg.sender,
            provider: _provider,
            evaluator: designatedEvaluator,
            budget: 0,
            expiry: _expiry,
            taskHash: _taskHash,
            deliverableHash: bytes32(0),
            status: JobStatus.Open,
            workerSplitBps: 0,
            exists: true
        });

        emit JobCreated(newJobId, msg.sender, _provider, designatedEvaluator, 0, _expiry);
        return newJobId;
    }

    /**
     * @notice ERC-8183: Step 2 - Client deposits funds into escrow
     */
    function fundJob(uint256 _jobId) external payable {
        Job storage job = jobs[_jobId];
        require(job.exists, "Job does not exist");
        require(job.status == JobStatus.Open, "Job not in Open state");
        require(msg.sender == job.client, "Only client can fund");
        require(msg.value > 0, "Funding must be > 0");

        job.budget = msg.value;
        job.status = JobStatus.Funded;

        emit JobFunded(_jobId, msg.value);
    }

    /**
     * @notice ERC-8183: Step 3 - Provider submits completed deliverable proof
     */
    function submitDeliverable(uint256 _jobId, bytes32 _deliverableHash) external {
        Job storage job = jobs[_jobId];
        require(job.exists, "Job does not exist");
        require(job.status == JobStatus.Funded, "Job not in Funded state");
        require(msg.sender == job.provider, "Only assigned provider can submit");
        require(_deliverableHash != bytes32(0), "Empty deliverable hash");

        job.deliverableHash = _deliverableHash;
        job.status = JobStatus.Submitted;

        emit JobSubmitted(_jobId, _deliverableHash);
    }

    /**
     * @notice ERC-8183: Step 4 - Evaluator resolves task with basis-point split
     * @dev No client override possible once in evaluation.
     */
    function evaluateJob(
        uint256 _jobId,
        uint256 _workerSplitBps,
        string calldata _rulingOpinion
    ) external {
        Job storage job = jobs[_jobId];
        require(job.exists, "Job does not exist");
        require(job.status == JobStatus.Submitted, "Job not awaiting evaluation");
        require(msg.sender == job.evaluator || msg.sender == courtGateway, "Unauthorized evaluator");
        require(_workerSplitBps <= 10000, "Invalid basis points (max 10000)");

        job.status = JobStatus.Terminal;
        job.workerSplitBps = _workerSplitBps;

        uint256 totalBudget = job.budget;
        uint256 workerAmount = (totalBudget * _workerSplitBps) / 10000;
        uint256 clientRefund = totalBudget - workerAmount;

        if (workerAmount > 0) {
            (bool successWorker, ) = payable(job.provider).call{value: workerAmount}("");
            require(successWorker, "Worker payout failed");
        }

        if (clientRefund > 0) {
            (bool successClient, ) = payable(job.client).call{value: clientRefund}("");
            require(successClient, "Client refund failed");
        }

        emit JobEvaluated(_jobId, _workerSplitBps, _rulingOpinion);
    }

    /**
     * @notice Expiry safeguard: If evaluator stalls past deadline, anyone can trigger client refund
     */
    function claimExpiredRefund(uint256 _jobId) external {
        Job storage job = jobs[_jobId];
        require(job.exists, "Job does not exist");
        require(job.status != JobStatus.Terminal, "Job already finalized");
        require(block.timestamp > job.expiry, "Job has not expired");

        job.status = JobStatus.Terminal;
        uint256 refundAmount = job.budget;
        job.budget = 0;

        if (refundAmount > 0) {
            (bool success, ) = payable(job.client).call{value: refundAmount}("");
            require(success, "Refund transfer failed");
        }

        emit JobRefunded(_jobId, "Job expired without completed evaluation");
    }
}
