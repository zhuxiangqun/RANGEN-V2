# Advanced Circuit Breaker Implementation Plan

为了实现带状态机的**高级熔断器 (Advanced Circuit Breaker)**，我们将引入一个专门的工具类来管理 DeepSeek API 的健康状态，并在 `LLMIntegration` 中集成它。

## 1. 新增核心组件: `CircuitBreaker`

我们将创建一个通用的熔断器类，实现完整的状态机逻辑。

* **文件**: `src/core/utils/circuit_breaker.py` (新文件)

* **状态机**:

  * `CLOSED` (正常): 允许所有请求。

  * `OPEN` (熔断): 拒绝所有请求，直接抛出异常。

  * `HALF_OPEN` (半开): 经过冷却期后，允许一次试探性请求。成功则关闭熔断，失败则继续熔断。

* **配置参数**:

  * `failure_threshold`: 触发熔断的连续失败次数 (e.g., 5)。

  * `recovery_timeout`: 熔断后的冷却时间 (e.g., 60秒)。

## 2. 集成熔断器: `LLMIntegration`

我们将修改 `LLMIntegration` 类，使其 API 调用受熔断器保护。

* **文件**: `src/core/llm_integration.py`

* **变更**:

  * 在 `__init__` 中初始化 `CircuitBreaker` 实例。

  * 修改 `_call_llm` 方法：

    * 使用 `self.circuit_breaker.call(self._execute_request, ...)` 包裹实际的 HTTP 请求。

    * 将 `requests.post` 逻辑提取为独立的 `_execute_request` 方法，以便熔断器调用。

    * 捕获 `CircuitBreakerOpenError`，并返回 `None` (或特定的错误标识)，以便上层 (`RealReasoningEngine`) 能够识别并触发降级。

## 3. 完善降级逻辑: `RealReasoningEngine`

利用之前 P4 阶段实现的降级逻辑，确保当 `LLMIntegration` 因熔断返回失败时，系统能平滑切换。

* **文件**: `src/core/real_reasoning_engine.py` (无需大改，只需确认能处理 Circuit Breaker 引发的失败)

* **逻辑确认**: 现有的 `try-except` 块已经能够捕获 `LLMIntegration` 的失败并回退到启发式评估或 Phi-3。

## 4. 实施步骤

1. **创建** **`src/core/utils/circuit_breaker.py`**: 实现状态机类。
2. **重构** **`src/core/llm_integration.py`**: 引入熔断器并重构请求逻辑。
3. **验证**: 运行测试，模拟 API 连续失败，验证熔断器是否进入 `OPEN` 状态并拒绝后续请求。

