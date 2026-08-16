// SPDX-License-Identifier: MIT
pragma solidity ^0.8.20;

interface IERC20 {
    function transfer(address to, uint256 amount) external returns (bool);
    function transferFrom(address from, address to, uint256 amount) external returns (bool);
    function balanceOf(address account) external view returns (uint256);
}

contract AgentEscrowV2 {
    enum TaskStatus { Created, Submitted, Resolved, Expired }

    struct Task {
        uint256 id;
        address client;
        address worker;
        uint256 amount;
        string detailsHash;
        uint256 deadline;
        TaskStatus status;
        string deliverable;
    }

    IERC20 public immutable paymentToken;
    address public immutable owner;
    address public treasury;
    uint256 public feeBps = 150; // 1.5% Protocol Fee (150 / 10000)

    uint256 public taskCount;
    mapping(uint256 => Task) public tasks;

    event TaskCreated(uint256 indexed taskId, address indexed client, address indexed worker, uint256 amount, uint256 deadline);
    event TaskSubmitted(uint256 indexed taskId, string deliverable);
    event TaskResolved(uint256 indexed taskId, uint256 clientPayout, uint256 workerPayout, uint256 feePaid);
    event TreasuryUpdated(address newTreasury);
    event FeeBpsUpdated(uint256 newFeeBps);

    modifier onlyOwner() {
        require(msg.sender == owner, "Only contract owner can execute");
        _;
    }

    constructor(address _paymentToken, address _treasury) {
        require(_paymentToken != address(0), "Invalid token address");
        require(_treasury != address(0), "Invalid treasury address");
        paymentToken = IERC20(_paymentToken);
        owner = msg.sender;
        treasury = _treasury;
    }

    function setTreasury(address _newTreasury) external onlyOwner {
        require(_newTreasury != address(0), "Invalid address");
        treasury = _newTreasury;
        emit TreasuryUpdated(_newTreasury);
    }

    function setFeeBps(uint256 _feeBps) external onlyOwner {
        require(_feeBps <= 1000, "Fee cannot exceed 10%");
        feeBps = _feeBps;
        emit FeeBpsUpdated(_feeBps);
    }

    function createTask(
        address _worker,
        uint256 _amount,
        string calldata _detailsHash,
        uint256 _durationSeconds
    ) external returns (uint256) {
        require(_worker != address(0), "Invalid worker address");
        require(_amount > 0, "Amount must be > 0");

        require(paymentToken.transferFrom(msg.sender, address(this), _amount), "USDC Transfer failed");

        taskCount++;
        uint256 deadline = block.timestamp + _durationSeconds;

        tasks[taskCount] = Task({
            id: taskCount,
            client: msg.sender,
            worker: _worker,
            amount: _amount,
            detailsHash: _detailsHash,
            deadline: deadline,
            status: TaskStatus.Created,
            deliverable: ""
        });

        emit TaskCreated(taskCount, msg.sender, _worker, _amount, deadline);
        return taskCount;
    }

    function submitTask(uint256 _taskId, string calldata _deliverable) external {
        Task storage task = tasks[_taskId];
        require(task.status == TaskStatus.Created, "Task not in Created state");
        require(msg.sender == task.worker, "Only designated worker can submit");
        require(block.timestamp <= task.deadline, "Task deadline passed");

        task.status = TaskStatus.Submitted;
        task.deliverable = _deliverable;

        emit TaskSubmitted(_taskId, _deliverable);
    }

    function resolveTask(uint256 _taskId, uint256 _clientSharePct) external {
        Task storage task = tasks[_taskId];
        require(task.status == TaskStatus.Submitted || task.status == TaskStatus.Created, "Task cannot be resolved");
        require(msg.sender == task.client || msg.sender == owner, "Unauthorized resolution");
        require(_clientSharePct <= 100, "Percentage cannot exceed 100");

        task.status = TaskStatus.Resolved;

        // Calculate Protocol Fee
        uint256 fee = (task.amount * feeBps) / 10000;
        uint256 netEscrow = task.amount - fee;

        // Calculate Split of Net Escrow
        uint256 clientPayout = (netEscrow * _clientSharePct) / 100;
        uint256 workerPayout = netEscrow - clientPayout;

        // Execute On-Chain Distributions
        if (fee > 0) {
            paymentToken.transfer(treasury, fee);
        }
        if (clientPayout > 0) {
            paymentToken.transfer(task.client, clientPayout);
        }
        if (workerPayout > 0) {
            paymentToken.transfer(task.worker, workerPayout);
        }

        emit TaskResolved(_taskId, clientPayout, workerPayout, fee);
    }
}
