// SPDX-License-Identifier: MIT
pragma solidity ^0.8.20;

interface IERC20 {
    function transfer(address to, uint256 amount) external returns (bool);
    function transferFrom(address from, address to, uint256 amount) external returns (bool);
}

contract AgentCourtEscrow {
    enum TaskState { Created, Submitted, Resolved }

    struct Task {
        address clientAgent;
        address workerAgent;
        uint256 amount;
        uint256 deadline;
        string taskDetailsHash;
        string deliverablesHash;
        TaskState state;
        uint8 clientRulingShare;
    }

    IERC20 public immutable usdcToken;
    address public owner;
    address public court;
    address public feeRecipient;
    uint256 public feeBasisPoints; // 100 bps = 1.00% (10,000 bps = 100%)
    
    uint256 public taskCount;
    mapping(uint256 => Task) public tasks;

    event TaskCreated(
        uint256 indexed taskId,
        address indexed client,
        address indexed worker,
        uint256 amount,
        uint256 deadline
    );
    event TaskSubmitted(uint256 indexed taskId, string deliverablesHash);
    event TaskResolved(
        uint256 indexed taskId,
        uint8 clientShare,
        uint256 clientPayout,
        uint256 workerPayout,
        uint256 feePaid
    );
    event TaskRefunded(uint256 indexed taskId, address indexed client, uint256 amount);
    event FeeConfigUpdated(address indexed newRecipient, uint256 newFeeBasisPoints);
    event CourtUpdated(address indexed newCourt);

    modifier onlyOwner() {
        require(msg.sender == owner, "AgentCourt: Only owner");
        _;
    }

    modifier onlyCourt() {
        require(msg.sender == court, "AgentCourt: Only designated Court can call this");
        _;
    }

    constructor(address _usdcToken, address _court) {
        require(_usdcToken != address(0), "Invalid USDC token address");
        require(_court != address(0), "Invalid court address");
        
        owner = msg.sender;
        court = _court;
        feeRecipient = msg.sender;
        feeBasisPoints = 100; // 1.00% default protocol fee
        usdcToken = IERC20(_usdcToken);
    }

    function setCourt(address _newCourt) external onlyOwner {
        require(_newCourt != address(0), "Invalid address");
        court = _newCourt;
        emit CourtUpdated(_newCourt);
    }

    function setFeeConfig(address _newRecipient, uint256 _newFeeBps) external onlyOwner {
        require(_newRecipient != address(0), "Invalid fee recipient");
        require(_newFeeBps <= 1000, "Fee cannot exceed 10%");
        feeRecipient = _newRecipient;
        feeBasisPoints = _newFeeBps;
        emit FeeConfigUpdated(_newRecipient, _newFeeBps);
    }

    function createTask(
        address _workerAgent,
        uint256 _amount,
        string memory _taskDetailsHash,
        uint256 _durationSeconds
    ) external {
        require(_amount > 0, "Escrow amount must be > 0");
        require(_workerAgent != address(0) && _workerAgent != msg.sender, "Invalid worker");
        require(_durationSeconds >= 60, "Duration must be at least 60 seconds");

        bool success = usdcToken.transferFrom(msg.sender, address(this), _amount);
        require(success, "USDC transfer failed. Check allowance.");

        taskCount++;
        uint256 taskDeadline = block.timestamp + _durationSeconds;

        tasks[taskCount] = Task({
            clientAgent: msg.sender,
            workerAgent: _workerAgent,
            amount: _amount,
            deadline: taskDeadline,
            taskDetailsHash: _taskDetailsHash,
            deliverablesHash: "",
            state: TaskState.Created,
            clientRulingShare: 0
        });

        emit TaskCreated(taskCount, msg.sender, _workerAgent, _amount, taskDeadline);
    }

    function submitTask(uint256 _taskId, string memory _deliverablesHash) external {
        Task storage task = tasks[_taskId];
        require(msg.sender == task.workerAgent, "Only assigned worker can submit");
        require(task.state == TaskState.Created, "Task not in Created state");
        require(block.timestamp <= task.deadline, "Task deadline has passed");

        task.deliverablesHash = _deliverablesHash;
        task.state = TaskState.Submitted;

        emit TaskSubmitted(_taskId, _deliverablesHash);
    }

    function claimRefund(uint256 _taskId) external {
        Task storage task = tasks[_taskId];
        require(msg.sender == task.clientAgent, "Only client can claim refund");
        require(task.state == TaskState.Created, "Task already submitted or resolved");
        require(block.timestamp > task.deadline, "Deadline has not passed yet");

        task.state = TaskState.Resolved;

        require(usdcToken.transfer(task.clientAgent, task.amount), "Refund transfer failed");

        emit TaskRefunded(_taskId, task.clientAgent, task.amount);
    }

    function resolveTask(uint256 _taskId, uint8 _clientRulingShare) external onlyCourt {
        Task storage task = tasks[_taskId];
        require(task.state == TaskState.Submitted, "Task not ready for resolution");
        require(_clientRulingShare <= 100, "Share must be 0-100");

        task.state = TaskState.Resolved;
        task.clientRulingShare = _clientRulingShare;

        uint256 total = task.amount;
        
        // 1. Calculate and take Protocol Fee (1%)
        uint256 fee = (total * feeBasisPoints) / 10000;
        uint256 distributable = total - fee;

        if (fee > 0) {
            require(usdcToken.transfer(feeRecipient, fee), "Protocol fee transfer failed");
        }

        // 2. Distribute remaining 99% according to AI verdict
        uint256 clientPayout = (distributable * _clientRulingShare) / 100;
        uint256 workerPayout = distributable - clientPayout;

        if (clientPayout > 0) {
            require(usdcToken.transfer(task.clientAgent, clientPayout), "Client payout failed");
        }
        if (workerPayout > 0) {
            require(usdcToken.transfer(task.workerAgent, workerPayout), "Worker payout failed");
        }

        emit TaskResolved(_taskId, _clientRulingShare, clientPayout, workerPayout, fee);
    }
}