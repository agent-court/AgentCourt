// SPDX-License-Identifier: MIT
pragma solidity ^0.8.20;

interface IERC20 {
    function transfer(address to, uint256 amount) external returns (bool);
    function transferFrom(address from, address to, uint256 amount) external returns (bool);
    function balanceOf(address account) external view returns (uint256);
}

contract AgentEscrowV5 {
    enum TaskState { Created, Funded, Started, Completed, Disputed, Settled }

    struct Task {
        uint256 taskId;
        address client;
        address worker;
        uint256 amount;
        bytes32 specHash;
        bytes32 deliverableHash;
        TaskState state;
        uint256 workerBps;
        bytes32 verdictHash;
    }

    IERC20 public immutable usdc;
    address public owner;
    address public arbitrator;
    uint256 public constant BPS_DENOMINATOR = 10000;
    uint256 public protocolFeeBps = 150; // 1.5%

    mapping(uint256 => Task) public tasks;
    uint256 public taskCounter;

    event TaskCreated(uint256 indexed taskId, address indexed client, address indexed worker, uint256 amount, bytes32 specHash);
    event TaskFunded(uint256 indexed taskId, uint256 amount);
    event TaskStarted(uint256 indexed taskId);
    event TaskCompleted(uint256 indexed taskId, bytes32 deliverableHash);
    event DisputeOpened(uint256 indexed taskId, address indexed openedBy);
    event DisputeResolved(uint256 indexed taskId, uint256 workerBps, bytes32 verdictHash);

    modifier onlyOwner() {
        require(msg.sender == owner, "Only owner");
        _;
    }

    modifier onlyArbitrator() {
        require(msg.sender == arbitrator || msg.sender == owner, "Only arbitrator");
        _;
    }

    constructor(address _usdc, address _arbitrator) {
        usdc = IERC20(_usdc);
        owner = msg.sender;
        arbitrator = _arbitrator;
    }

    function setArbitrator(address _arbitrator) external onlyOwner {
        arbitrator = _arbitrator;
    }

    function createTask(address worker, uint256 amount, bytes32 specHash) external returns (uint256) {
        taskCounter++;
        uint256 taskId = taskCounter;

        tasks[taskId] = Task({
            taskId: taskId,
            client: msg.sender,
            worker: worker,
            amount: amount,
            specHash: specHash,
            deliverableHash: bytes32(0),
            state: TaskState.Created,
            workerBps: 0,
            verdictHash: bytes32(0)
        });

        emit TaskCreated(taskId, msg.sender, worker, amount, specHash);
        return taskId;
    }

    function fundTask(uint256 taskId) external {
        Task storage task = tasks[taskId];
        require(task.state == TaskState.Created, "Invalid state");
        require(msg.sender == task.client, "Only client can fund");

        task.state = TaskState.Funded;
        require(usdc.transferFrom(msg.sender, address(this), task.amount), "USDC transfer failed");

        emit TaskFunded(taskId, task.amount);
    }

    function startTask(uint256 taskId) external {
        Task storage task = tasks[taskId];
        require(task.state == TaskState.Funded, "Invalid state");
        require(msg.sender == task.worker, "Only worker can start");

        task.state = TaskState.Started;
        emit TaskStarted(taskId);
    }

    function completeTask(uint256 taskId, bytes32 deliverableHash) external {
        Task storage task = tasks[taskId];
        require(task.state == TaskState.Started, "Invalid state");
        require(msg.sender == task.worker, "Only worker can complete");

        task.deliverableHash = deliverableHash;
        task.state = TaskState.Completed;
        emit TaskCompleted(taskId, deliverableHash);
    }

    function openDispute(uint256 taskId) external {
        Task storage task = tasks[taskId];
        require(task.state == TaskState.Completed || task.state == TaskState.Started, "Invalid state for dispute");
        require(msg.sender == task.client || msg.sender == task.worker, "Unauthorized");

        task.state = TaskState.Disputed;
        emit DisputeOpened(taskId, msg.sender);
    }

    function resolveDispute(uint256 taskId, uint256 workerBps, bytes32 verdictHash) external onlyArbitrator {
        Task storage task = tasks[taskId];
        require(task.state == TaskState.Disputed, "Task not in dispute");
        require(workerBps <= BPS_DENOMINATOR, "Invalid BPS");

        task.state = TaskState.Settled;
        task.workerBps = workerBps;
        task.verdictHash = verdictHash;

        uint256 total = task.amount;
        uint256 fee = (total * protocolFeeBps) / BPS_DENOMINATOR;
        uint256 distributable = total - fee;

        uint256 workerShare = (distributable * workerBps) / BPS_DENOMINATOR;
        uint256 clientShare = distributable - workerShare;

        if (fee > 0) {
            usdc.transfer(owner, fee);
        }
        if (workerShare > 0) {
            usdc.transfer(task.worker, workerShare);
        }
        if (clientShare > 0) {
            usdc.transfer(task.client, clientShare);
        }

        emit DisputeResolved(taskId, workerBps, verdictHash);
    }
}
