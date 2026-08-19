// SPDX-License-Identifier: MIT
pragma solidity ^0.8.20;

import "@openzeppelin/contracts/access/AccessControl.sol";
import "@openzeppelin/contracts/utils/ReentrancyGuard.sol";
import "@openzeppelin/contracts/utils/Pausable.sol";

/**
 * @title AgentEscrowV3
 * @notice Production-grade multi-agent escrow with multi-LLM jury arbitration on Base.
 */
contract AgentEscrowV3 is AccessControl, ReentrancyGuard, Pausable {
    bytes32 public constant COURT_ROLE = keccak256("COURT_ROLE");
    bytes32 public constant ADMIN_ROLE = keccak256("ADMIN_ROLE");

    uint256 public constant BPS_DENOMINATOR = 10000;
    uint256 public constant MIN_CHALLENGE_PERIOD = 1 hours;
    uint256 public constant MAX_CHALLENGE_PERIOD = 7 days;

    enum TaskStatus {
        Created,
        Active,
        Completed,
        Disputed,
        RulingProposed,
        Resolved,
        Refunded
    }

    struct Task {
        uint256 id;
        address client;
        address contractor;
        uint256 amount;
        string specHash;           // IPFS CID or hash of specifications
        uint256 challengePeriod;   // Seconds allowed to dispute a proposed ruling
        TaskStatus status;
        uint256 contractorBps;     // Basis points (0 - 10000) awarded to contractor
        uint256 rulingProposedAt;
        string verdictCid;         // IPFS CID of multi-LLM juror reasoning
    }

    uint256 public taskCounter;
    mapping(uint256 => Task) public tasks;

    event TaskCreated(uint256 indexed taskId, address indexed client, address indexed contractor, uint256 amount, string specHash);
    event TaskDisputed(uint256 indexed taskId, address indexed initiator, string evidenceCid);
    event RulingProposed(uint256 indexed taskId, uint256 contractorBps, string verdictCid, uint256 unlockTimestamp);
    event TaskResolved(uint256 indexed taskId, uint256 contractorPayout, uint256 clientRefund);
    event TaskRefunded(uint256 indexed taskId, uint256 amount);

    constructor(address initialAdmin, address initialCourt) {
        _grantRole(DEFAULT_ADMIN_ROLE, initialAdmin);
        _grantRole(ADMIN_ROLE, initialAdmin);
        _grantRole(COURT_ROLE, initialCourt);
    }

    function createTask(
        address _contractor,
        string calldata _specHash,
        uint256 _challengePeriod
    ) external payable whenNotPaused nonReentrant returns (uint256) {
        require(msg.value > 0, "Escrow amount must be > 0");
        require(_contractor != address(0) && _contractor != msg.sender, "Invalid contractor address");
        require(_challengePeriod >= MIN_CHALLENGE_PERIOD && _challengePeriod <= MAX_CHALLENGE_PERIOD, "Invalid challenge window");

        taskCounter++;
        uint256 taskId = taskCounter;

        tasks[taskId] = Task({
            id: taskId,
            client: msg.sender,
            contractor: _contractor,
            amount: msg.value,
            specHash: _specHash,
            challengePeriod: _challengePeriod,
            status: TaskStatus.Active,
            contractorBps: 0,
            rulingProposedAt: 0,
            verdictCid: ""
        });

        emit TaskCreated(taskId, msg.sender, _contractor, msg.value, _specHash);
        return taskId;
    }

    function raiseDispute(uint256 _taskId, string calldata _evidenceCid) external nonReentrant {
        Task storage task = tasks[_taskId];
        require(task.status == TaskStatus.Active, "Task not active");
        require(msg.sender == task.client || msg.sender == task.contractor, "Unauthorized");

        task.status = TaskStatus.Disputed;
        emit TaskDisputed(_taskId, msg.sender, _evidenceCid);
    }

    function proposeRuling(
        uint256 _taskId,
        uint256 _contractorBps,
        string calldata _verdictCid
    ) external onlyRole(COURT_ROLE) {
        Task storage task = tasks[_taskId];
        require(task.status == TaskStatus.Disputed, "Task not in dispute");
        require(_contractorBps <= BPS_DENOMINATOR, "Bps exceeds 100%");

        task.status = TaskStatus.RulingProposed;
        task.contractorBps = _contractorBps;
        task.rulingProposedAt = block.timestamp;
        task.verdictCid = _verdictCid;

        emit RulingProposed(_taskId, _contractorBps, _verdictCid, block.timestamp + task.challengePeriod);
    }

    function executeRuling(uint256 _taskId) external nonReentrant {
        Task storage task = tasks[_taskId];
        require(task.status == TaskStatus.RulingProposed, "No ruling proposed");
        require(block.timestamp >= task.rulingProposedAt + task.challengePeriod, "Challenge window active");

        task.status = TaskStatus.Resolved;

        uint256 contractorPayout = (task.amount * task.contractorBps) / BPS_DENOMINATOR;
        uint256 clientRefund = task.amount - contractorPayout;

        if (contractorPayout > 0) {
            (bool sentContractor, ) = payable(task.contractor).call{value: contractorPayout}("");
            require(sentContractor, "Contractor transfer failed");
        }
        if (clientRefund > 0) {
            (bool sentClient, ) = payable(task.client).call{value: clientRefund}("");
            require(sentClient, "Client transfer failed");
        }

        emit TaskResolved(_taskId, contractorPayout, clientRefund);
    }

    function completeTask(uint256 _taskId) external nonReentrant {
        Task storage task = tasks[_taskId];
        require(msg.sender == task.client, "Only client can complete");
        require(task.status == TaskStatus.Active, "Task not active");

        task.status = TaskStatus.Completed;
        (bool sent, ) = payable(task.contractor).call{value: task.amount}("");
        require(sent, "Transfer failed");

        emit TaskResolved(_taskId, task.amount, 0);
    }

    function pause() external onlyRole(ADMIN_ROLE) { _pause(); }
    function unpause() external onlyRole(ADMIN_ROLE) { _unpause(); }
}
