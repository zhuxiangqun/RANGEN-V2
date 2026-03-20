"""
Swarm 文件系统收件箱

实现 Agent 之间的消息传递:
- 点对点消息
- 广播消息
- 消息查看 (peek，不消费)
- 消息接收 (receive，消费)
"""

import json
import uuid
from pathlib import Path
from datetime import datetime
from typing import List, Optional, Dict, Any
from dataclasses import dataclass, asdict


@dataclass
class Message:
    """消息"""
    id: str
    from_agent: str
    to_agent: str  # "*" 表示广播
    content: str
    timestamp: str
    type: str = "direct"  # direct / broadcast
    metadata: Dict[str, Any] = None
    
    def __post_init__(self):
        if self.metadata is None:
            self.metadata = {}
    
    def to_dict(self) -> dict:
        return asdict(self)
    
    @classmethod
    def from_dict(cls, data: dict) -> "Message":
        return cls(**data)


class FileInbox:
    """
    文件系统收件箱
    
    存储结构:
    .swarm/
    └── {team}/
        └── inbox/
            ├── leader/
            │   ├── 001.json
            │   └── 002.json
            ├── worker1/
            └── broadcast/
    
    使用方式:
        inbox = FileInbox(".swarm")
        inbox.send("my-team", "leader", "worker1", "任务完成")
        messages = inbox.receive("my-team", "leader")
    """
    
    def __init__(self, base_dir: str = ".swarm"):
        self.base_dir = Path(base_dir)
    
    def _get_inbox_path(self, team: str, agent: str) -> Path:
        """获取 Agent 收件箱路径"""
        return self.base_dir / team / "inbox" / agent
    
    def _ensure_inbox(self, team: str, agent: str) -> Path:
        """确保收件箱目录存在"""
        path = self._get_inbox_path(team, agent)
        path.mkdir(parents=True, exist_ok=True)
        return path
    
    def send(
        self,
        team: str,
        to_agent: str,
        content: str,
        from_agent: str = "system",
        msg_type: str = "direct",
        metadata: Optional[Dict[str, Any]] = None
    ) -> str:
        """
        发送消息
        
        Args:
            team: 团队名
            to_agent: 接收者 ("*" 表示广播给所有)
            content: 消息内容
            from_agent: 发送者
            msg_type: 消息类型 (direct/broadcast)
            metadata: 额外元数据
            
        Returns:
            消息ID
        """
        msg = Message(
            id=str(uuid.uuid4())[:8],
            from_agent=from_agent,
            to_agent=to_agent,
            content=content,
            timestamp=datetime.now().isoformat(),
            type=msg_type,
            metadata=metadata or {}
        )
        
        # 广播消息存到 broadcast 目录
        if to_agent == "*":
            target = "broadcast"
        else:
            target = to_agent
        
        inbox_path = self._ensure_inbox(team, target)
        
        # 保存消息
        msg_file = inbox_path / f"{msg.id}.json"
        with open(msg_file, "w", encoding="utf-8") as f:
            json.dump(msg.to_dict(), f, ensure_ascii=False, indent=2)
        
        return msg.id
    
    def receive(self, team: str, agent: str, limit: int = 50) -> List[Message]:
        """
        接收并消费消息 (读取后删除)
        
        Args:
            team: 团队名
            agent: Agent 名
            limit: 最大消息数
            
        Returns:
            消息列表
        """
        inbox_path = self._get_inbox_path(team, agent)
        
        if not inbox_path.exists():
            return []
        
        messages = []
        for msg_file in sorted(inbox_path.glob("*.json"))[:limit]:
            try:
                with open(msg_file, encoding="utf-8") as f:
                    data = json.load(f)
                    messages.append(Message.from_dict(data))
                # 消费后删除
                msg_file.unlink()
            except Exception:
                continue
        
        return messages
    
    def peek(self, team: str, agent: str, limit: int = 50) -> List[Message]:
        """
        查看消息 (不消费)
        
        Args:
            team: 团队名
            agent: Agent 名
            limit: 最大消息数
            
        Returns:
            消息列表
        """
        inbox_path = self._get_inbox_path(team, agent)
        
        if not inbox_path.exists():
            return []
        
        messages = []
        for msg_file in sorted(inbox_path.glob("*.json"))[:limit]:
            try:
                with open(msg_file, encoding="utf-8") as f:
                    data = json.load(f)
                    messages.append(Message.from_dict(data))
            except Exception:
                continue
        
        return messages
    
    def count(self, team: str, agent: str) -> int:
        """获取未读消息数"""
        inbox_path = self._get_inbox_path(team, agent)
        if not inbox_path.exists():
            return 0
        return len(list(inbox_path.glob("*.json")))
    
    def broadcast(self, team: str, from_agent: str, content: str, metadata: Optional[Dict[str, Any]] = None) -> str:
        """
        广播消息给所有团队成员
        
        Args:
            team: 团队名
            from_agent: 发送者
            content: 消息内容
            metadata: 额外元数据
            
        Returns:
            消息ID
        """
        return self.send(
            team=team,
            to_agent="*",
            content=content,
            from_agent=from_agent,
            msg_type="broadcast",
            metadata=metadata
        )
    
    def list_agents(self, team: str) -> List[str]:
        """列出团队所有 Agent"""
        inbox_dir = self.base_dir / team / "inbox"
        if not inbox_dir.exists():
            return []
        return [p.name for p in inbox_dir.iterdir() if p.is_dir() and p.name != "broadcast"]
    
    def cleanup(self, team: str) -> None:
        """清理团队收件箱"""
        import shutil
        inbox_dir = self.base_dir / team / "inbox"
        if inbox_dir.exists():
            shutil.rmtree(inbox_dir)


# =============================================================================
# 使用示例
# =============================================================================

if __name__ == "__main__":
    inbox = FileInbox("/tmp/.swarm-test")
    
    # 清理测试环境
    inbox.cleanup("test-team")
    
    # 发送消息
    msg_id = inbox.send("test-team", "leader", "你好 leader，我是 worker1")
    print(f"发送消息: {msg_id}")
    
    # 广播
    broadcast_id = inbox.broadcast("test-team", "leader", "全体注意：会议5分钟后开始")
    print(f"广播: {broadcast_id}")
    
    # 查看消息
    leader_messages = inbox.peek("test-team", "leader")
    print(f"\nleader 待收消息 ({len(leader_messages)}条):")
    for msg in leader_messages:
        print(f"  - [{msg.type}] {msg.from_agent}: {msg.content}")
    
    # 接收消息
    received = inbox.receive("test-team", "leader")
    print(f"\n已接收并消费 {len(received)} 条消息")
    
    # 检查未读
    print(f"剩余未读: {inbox.count('test-team', 'leader')}")
