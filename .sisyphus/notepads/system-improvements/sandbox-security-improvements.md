# AI Agent 沙箱安全改进方案

**创建时间**: 2026-03-03  
**基于参考**: [AI Agent Sandboxing Best Practices](https://levelup.gitconnected.com/a-technical-guide-to-ai-agent-sandboxing-dfdf9571dd2d)

---

## 一、当前实现评估

### 已有的安全措施
| 功能 | 状态 | 说明 |
|------|------|------|
| 超时保护 | ✅ | 30秒 |
| 内存限制 | ✅ | 256MB |
| 文件系统限制 | ✅ | allowed_dirs, blocked_dirs |
| 网络标志 | ✅ | allow_network flag |
| 敏感词检测 | ✅ | security_control.py |
| 外发确认 | ✅ | outbound confirmation |
| Docker选项 | ⚠️ | 已配置但默认关闭 |

### 关键差距
1. **Docker隔离未启用** - 默认在主机环境执行
2. **网络隔离弱** - 仅标志位，无强制执行
3. **进程隔离不足** - 使用threading，非真正隔离
4. **工作目录可写** - 应改为只读+临时
5. **资源配额不全** - 缺少CPU/网络配额

---

## 二、改进方案

### 1. Docker沙箱启用 (优先级: 高)

**当前**: `use_docker: bool = False`  
**改进**: 默认启用，使用最小化镜像

```python
# gateway/sandbox/__init__.py
@dataclass
class SandboxConfig:
    use_docker: bool = True  # 改为默认True
    docker_image: str = "python:3.11-slim"  # 使用 slim 镜像减少攻击面
    docker_network: str = "none"  # 完全禁用网络
    read_only_rootfs: bool = True  # 根文件系统只读
    auto_remove: bool = True  # 执行后自动清理
```

### 2. 文件系统隔离强化 (优先级: 高)

**原则**: 
- 只读访问工作目录
- 临时文件使用tmpfs
- 禁止访问系统目录

```python
# 改进后的配置
allowed_dirs: List[str] = field(default_factory=lambda: ["data/workspace"])
read_only_dirs: List[str] = field(default_factory=lambda: ["data/workspace"])
temp_dirs: List[str] = field(default_factory=lambda: ["/tmp/sandbox"])
blocked_dirs: List[str] = field(default_factory=lambda: [
    "/", "~", "/etc", "/usr", "/var", "/root", 
    "/home", "/opt", "/boot", "/dev"
])
```

### 3. 网络隔离实现 (优先级: 高)

**方案**: 使用代理强制执行域名限制

```python
# 新增网络代理配置
network_proxy_url: Optional[str] = None  # 代理服务器URL
allowed_domains: List[str] = field(default_factory=list)  # 允许的域名
blocked_domains: List[str] = field(default_factory=list)  # 禁止的域名
dns_servers: List[str] = field(default_factory=lambda: ["8.8.8.8"])
```

### 4. 资源配额完善 (优先级: 中)

```python
# 新增资源限制
max_cpu_percent: int = 50  # CPU限制
max_network_bandwidth_mb: int = 10  # 网络带宽
max_disk_write_mb: int = 100  # 磁盘写入
max_file_descriptors: int = 100  # 文件描述符限制
```

### 5. 危险命令过滤增强 (优先级: 中)

```python
# 扩展危险命令列表
DANGEROUS_COMMANDS = [
    "rm -rf", "mkfs", "dd", "fdisk",  # 磁盘操作
    "curl", "wget", "nc", "ncat", "ssh",  # 网络下载/连接
    "chmod 777", "chown", "sudo", "su",  # 权限操作
    "kill -9", "pkill",  # 进程终止
    "export", "source",  # 环境变量
    "eval", "exec",  # 命令执行
    "python -m", "pip install", "apt", "yum",  # 包管理
]
```

### 6. 执行后清理 (优先级: 中)

```python
async def cleanup(self):
    """执行后清理"""
    # 删除临时文件
    # 清理环境变量
    # 关闭网络连接
    # 记录审计日志
```

---

## 三、实施方案

### Phase 1: 紧急改进 (1-2周)
1. ✅ 启用Docker沙箱（默认开启）
2. ✅ 强化文件系统只读限制
3. ✅ 完善危险命令过滤

### Phase 2: 中期改进 (2-4周)
1. 实现网络代理隔离
2. 添加资源配额
3. 完善审计日志

### Phase 3: 长期改进 (1-2月)
1. 集成gVisor
2. 考虑WebAssembly隔离
3. 实施Zero-Trust网络

---

## 四、关键文件修改清单

| 文件 | 修改内容 |
|------|----------|
| `src/gateway/sandbox/__init__.py` | 强化配置，启用Docker |
| `src/gateway/tools/code_executor.py` | 集成强化沙箱 |
| `src/services/sandbox_service.py` | 同步配置改进 |
| `src/services/security_control.py` | 增强网络隔离 |

---

## 五、验证检查清单

- [ ] Docker沙箱执行成功
- [ ] 文件系统只读限制有效
- [ ] 网络请求被正确拦截
- [ ] 危险命令被过滤
- [ ] 超时/内存限制生效
- [ ] 执行后临时文件被清理
- [ ] 审计日志完整记录

---

## 六、参考资源

- [A Technical Guide to AI Agent Sandboxing](https://levelup.gitconnected.com/a-technical-guide-to-ai-agent-sandboxing-dfdf9571dd2d)
- [Claude Code Sandboxing](https://www.anthropic.com/engineering/claude-code-sandboxing)
- [OpenSandbox Deployment Guide](https://www.ahhhhfs.com/79118/)
- [gVisor Documentation](https://gvisor.dev/docs/)
- [Docker Security](https://docs.docker.com/engine/security/)
