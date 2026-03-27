// SPDX-License-Identifier: MIT
pragma solidity ^0.8.20;

import "@openzeppelin/contracts/proxy/Clones.sol";
import "@openzeppelin/contracts/token/ERC20/IERC20.sol";
import "@openzeppelin/contracts/token/ERC20/utils/SafeERC20.sol";

contract AgentWallet {
    using SafeERC20 for IERC20;

    error AlreadyInitialized();
    error NotOwner();
    error NotExecutor();
    error Paused();
    error ZeroAddress();
    error InsufficientEthBalance();
    error DailyEthLimitExceeded();
    error DailyTokenLimitExceeded();
    error EthTransferFailed();

    address public owner;
    address public executor;
    address public factory;

    bool public initialized;
    bool public walletPaused;

    uint256 public dailyEthLimit;
    uint256 public ethSpentToday;
    uint256 public ethLastReset;

    mapping(address => uint256) public dailyTokenLimit;
    mapping(address => uint256) public tokenSpentToday;
    mapping(address => uint256) public tokenLastReset;

    event Initialized(address indexed owner, address indexed executor);
    event DepositETH(address indexed from, uint256 amount);
    event WithdrawETH(address indexed to, uint256 amount);
    event WithdrawERC20(address indexed token, address indexed to, uint256 amount);

    event ExecutorUpdated(address indexed oldExecutor, address indexed newExecutor);
    event WalletPaused();
    event WalletUnpaused();
    event DailyEthLimitUpdated(uint256 oldLimit, uint256 newLimit);
    event DailyTokenLimitUpdated(address indexed token, uint256 oldLimit, uint256 newLimit);

    event ExecutedETH(address indexed target, uint256 value, bytes data, bytes result);
    event ExecutedERC20Transfer(address indexed token, address indexed to, uint256 amount);
    event ExecutedContractCall(address indexed target, uint256 ethValue, bytes data, bytes result);

    modifier onlyOwner() {
        if (msg.sender != owner) revert NotOwner();
        _;
    }

    modifier onlyExecutor() {
        if (msg.sender != executor) revert NotExecutor();
        _;
    }

    modifier whenNotPaused() {
        if (walletPaused) revert Paused();
        _;
    }

    function initialize(
        address _owner,
        address _executor,
        uint256 _dailyEthLimit
    ) external {
        if (initialized) revert AlreadyInitialized();
        if (_owner == address(0) || _executor == address(0)) revert ZeroAddress();

        initialized = true;
        owner = _owner;
        executor = _executor;
        factory = msg.sender;
        dailyEthLimit = _dailyEthLimit;
        ethLastReset = block.timestamp;
        walletPaused = false;

        emit Initialized(_owner, _executor);
    }

    receive() external payable {
        emit DepositETH(msg.sender, msg.value);
    }

    function depositETH() external payable {
        emit DepositETH(msg.sender, msg.value);
    }

    function getEthBalance() external view returns (uint256) {
        return address(this).balance;
    }

    function getTokenBalance(address token) external view returns (uint256) {
        return IERC20(token).balanceOf(address(this));
    }

    function updateExecutor(address newExecutor) external onlyOwner {
        if (newExecutor == address(0)) revert ZeroAddress();
        address old = executor;
        executor = newExecutor;
        emit ExecutorUpdated(old, newExecutor);
    }

    function pauseWallet() external onlyOwner {
        walletPaused = true;
        emit WalletPaused();
    }

    function unpauseWallet() external onlyOwner {
        walletPaused = false;
        emit WalletUnpaused();
    }


    function updateDailyEthLimit(uint256 newLimit) external onlyOwner {
        uint256 old = dailyEthLimit;
        dailyEthLimit = newLimit;
        emit DailyEthLimitUpdated(old, newLimit);
    }

    function updateDailyTokenLimit(address token, uint256 newLimit) external onlyOwner {
        if (token == address(0)) revert ZeroAddress();
        uint256 old = dailyTokenLimit[token];
        dailyTokenLimit[token] = newLimit;
        emit DailyTokenLimitUpdated(token, old, newLimit);
    }

    function withdrawETH(uint256 amount) public onlyOwner {
        if (address(this).balance < amount) revert InsufficientEthBalance();

        (bool ok, ) = payable(owner).call{value: amount}("");
        if (!ok) revert EthTransferFailed();

        emit WithdrawETH(owner, amount);
    }

    function withdrawERC20(address token, uint256 amount) external onlyOwner {
        if (token == address(0)) revert ZeroAddress();
        IERC20(token).safeTransfer(owner, amount);
        emit WithdrawERC20(token, owner, amount);
    }

    /**
     * @dev Removes the wallet from service and returns all funds to owner.
     * Use this instead of selfdestruct which is deprecated/unreliable on some networks.
     */
    function decommission() external {
        if (msg.sender != factory) revert NotOwner();
        
        // Return all funds to owner
        uint256 balance = address(this).balance;
        if (balance > 0) {
            (bool ok, ) = payable(owner).call{value: balance}("");
            require(ok, "Transfer failed during decommission");
        }

        // Reset state so it can be re-initialized if needed, 
        // and it won't be usable anymore by the current owner/executor.
        initialized = false;
        owner = address(0);
        executor = address(0);
        walletPaused = true;
    }

    function executeETH(
        address payable target,
        uint256 amount,
        bytes calldata data
    ) external onlyExecutor whenNotPaused returns (bytes memory result) {
        if (target == address(0)) revert ZeroAddress();
        if (address(this).balance < amount) revert InsufficientEthBalance();

        _resetEthSpendIfNeeded();
        if (ethSpentToday + amount > dailyEthLimit) revert DailyEthLimitExceeded();

        ethSpentToday += amount;

        (bool success, bytes memory res) = target.call{value: amount}(data);
        if (!success) revert EthTransferFailed();

        emit ExecutedETH(target, amount, data, res);
        return res;
    }

    function executeERC20Transfer(
        address token,
        address to,
        uint256 amount
    ) external onlyExecutor whenNotPaused {
        if (token == address(0) || to == address(0)) revert ZeroAddress();

        _resetTokenSpendIfNeeded(token);
        if (tokenSpentToday[token] + amount > dailyTokenLimit[token]) {
            revert DailyTokenLimitExceeded();
        }

        tokenSpentToday[token] += amount;
        IERC20(token).safeTransfer(to, amount);

        emit ExecutedERC20Transfer(token, to, amount);
    }

    function executeContractCall(
        address target,
        uint256 ethValue,
        bytes calldata data
    ) external onlyExecutor whenNotPaused returns (bytes memory result) {
        if (target == address(0)) revert ZeroAddress();

        if (ethValue > 0) {
            if (address(this).balance < ethValue) revert InsufficientEthBalance();
            _resetEthSpendIfNeeded();
            if (ethSpentToday + ethValue > dailyEthLimit) revert DailyEthLimitExceeded();
            ethSpentToday += ethValue;
        }

        (bool success, bytes memory res) = target.call{value: ethValue}(data);
        require(success, "Contract call failed");

        emit ExecutedContractCall(target, ethValue, data, res);
        return res;
    }

    function approveERC20(
        address token,
        address spender,
        uint256 amount
    ) external onlyOwner {
        if (token == address(0) || spender == address(0)) revert ZeroAddress();
        IERC20(token).approve(spender, amount);
    }

    function _resetEthSpendIfNeeded() internal {
        if (block.timestamp >= ethLastReset + 1 days) {
            ethSpentToday = 0;
            ethLastReset = block.timestamp;
        }
    }

    function _resetTokenSpendIfNeeded(address token) internal {
        if (block.timestamp >= tokenLastReset[token] + 1 days) {
            tokenSpentToday[token] = 0;
            tokenLastReset[token] = block.timestamp;
        }
    }
}

contract AgentWalletFactory {
    using Clones for address;

    error ZeroAddress();
    error WalletAlreadyExists();

    address public immutable implementation;

    mapping(address => address) public userWallet;

    event WalletCreated(
        address indexed user,
        address indexed wallet,
        address indexed executor,
        uint256 dailyEthLimit
    );
    event WalletDeleted(address indexed user, address indexed wallet);

    constructor() {
        implementation = address(new AgentWallet());
    }

    function createWallet(address _executor, uint256 dailyEthLimit) external returns (address wallet) {
        if (userWallet[msg.sender] != address(0)) revert WalletAlreadyExists();

        wallet = implementation.clone();
        AgentWallet(payable(wallet)).initialize(
            msg.sender,
            _executor,
            dailyEthLimit
        );

        userWallet[msg.sender] = wallet;

        emit WalletCreated(msg.sender, wallet, _executor, dailyEthLimit);
    }

    function getMyWallet() external view returns (address) {
        return userWallet[msg.sender];
    }

    /**
     * @dev Decommissions the user's wallet and clears the mapping.
     */
    function deleteWallet() external {
        address wallet = userWallet[msg.sender];
        if (wallet == address(0)) revert ZeroAddress();
        
        AgentWallet(payable(wallet)).decommission();
        delete userWallet[msg.sender];
        
        emit WalletDeleted(msg.sender, wallet);
    }
}