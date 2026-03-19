#!/usr/bin/env python3
"""
Email Hand - 邮件操作能力包

支持：
- IMAP 接收邮件
- SMTP 发送邮件
- 邮件搜索
- 标记已读/未读
"""

import imaplib
import smtplib
import email
from email.header import decode_header
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.base import MIMEBase
from email import encoders
import logging
from typing import Dict, Any, List, Optional
from datetime import datetime

from .base import BaseHand, HandCategory, HandSafetyLevel, HandExecutionResult

logger = logging.getLogger(__name__)


class EmailHand(BaseHand):
    """邮件操作Hand - 支持IMAP接收和SMTP发送"""
    
    def __init__(self):
        super().__init__(
            name="email",
            description="邮件操作能力：接收、发送、搜索、标记",
            category=HandCategory.API_INTEGRATION,
            safety_level=HandSafetyLevel.MODERATE
        )
        self.logger = logger
        self._imap_connection = None
        self._smtp_connection = None
    
    def validate_parameters(self, **kwargs) -> bool:
        operation = kwargs.get("operation")
        required_operations = ["fetch_unread", "send", "search", "mark_read", "list_folders"]
        if operation and operation not in required_operations:
            return False
        return True
    
    async def execute(self, **kwargs) -> HandExecutionResult:
        try:
            if not self.validate_parameters(**kwargs):
                return HandExecutionResult(
                    hand_name=self.name,
                    success=False,
                    output={},
                    error="参数验证失败"
                )
            
            operation = kwargs.get("operation", "fetch_unread")
            
            if operation == "fetch_unread":
                result = await self._fetch_unread_emails(kwargs)
            elif operation == "send":
                result = await self._send_email(kwargs)
            elif operation == "search":
                result = await self._search_emails(kwargs)
            elif operation == "mark_read":
                result = await self._mark_as_read(kwargs)
            elif operation == "list_folders":
                result = await self._list_folders(kwargs)
            else:
                result = {"error": f"未知操作: {operation}"}
            
            return HandExecutionResult(
                hand_name=self.name,
                success=True,
                output=result
            )
            
        except Exception as e:
            self.logger.error(f"邮件操作失败: {e}")
            return HandExecutionResult(
                hand_name=self.name,
                success=False,
                output={},
                error=str(e)
            )
    
    async def _fetch_unread_emails(self, kwargs: Dict[str, Any]) -> Dict[str, Any]:
        """获取未读邮件"""
        imap_host = kwargs.get("imap_host") or ""
        imap_port = kwargs.get("imap_port", 993)
        username = kwargs.get("username") or ""
        password = kwargs.get("password") or ""
        mailbox = kwargs.get("mailbox", "INBOX")
        limit = kwargs.get("limit", 10)
        
        if not all([imap_host, username, password]):
            return {"error": "缺少必要的IMAP配置参数"}
        
        try:
            # 连接IMAP服务器
            if imap_port == 993:
                mail = imaplib.IMAP4_SSL(str(imap_host), imap_port)
            else:
                mail = imaplib.IMAP4(str(imap_host), imap_port)
            
            mail.login(str(username), str(password))
            mail.select(mailbox)
            
            # 搜索未读邮件
            status, messages = mail.search(None, "UNSEEN")
            
            if status != "OK":
                return {"error": "搜索邮件失败", "count": 0}
            
            email_ids = messages[0].split()
            total_unread = len(email_ids)
            
            # 限制数量
            email_ids = email_ids[-limit:] if len(email_ids) > limit else email_ids
            
            emails = []
            for email_id in email_ids:
                status, msg_data = mail.fetch(email_id, "(RFC822)")
                
                if status == "OK" and msg_data and len(msg_data) > 0:
                    msg_item = msg_data[0]
                    if msg_item and len(msg_item) > 1:
                        msg_bytes = msg_item[1]
                        if msg_bytes and isinstance(msg_bytes, bytes):
                            msg = email.message_from_bytes(msg_bytes)
                            email_data = self._parse_email(msg)
                            emails.append(email_data)
            
            mail.logout()
            
            return {
                "total_unread": total_unread,
                "fetched": len(emails),
                "emails": emails
            }
            
        except Exception as e:
            return {"error": f"获取邮件失败: {e}"}
    
    async def _send_email(self, kwargs: Dict[str, Any]) -> Dict[str, Any]:
        """发送邮件"""
        smtp_host = kwargs.get("smtp_host") or ""
        smtp_port = kwargs.get("smtp_port", 587)
        username = kwargs.get("username") or ""
        password = kwargs.get("password") or ""
        to_addr = kwargs.get("to")
        subject = kwargs.get("subject", "")
        body = kwargs.get("body", "")
        is_html = kwargs.get("is_html", False)
        
        if not all([smtp_host, username, password, to_addr]):
            return {"error": "缺少必要的SMTP配置参数"}
        
        try:
            # 创建邮件
            msg = MIMEMultipart()
            msg['From'] = str(username)
            msg['To'] = str(to_addr) if to_addr else ""
            msg['Subject'] = subject
            msg['Date'] = datetime.now().strftime("%a, %d %b %Y %H:%M:%S +0800")
            
            # 添加正文
            content_type = 'html' if is_html else 'plain'
            msg.attach(MIMEText(body, content_type, 'utf-8'))
            
            # 发送邮件
            smtp_host_str = str(smtp_host) if smtp_host else ""
            username_str = str(username) if username else ""
            password_str = str(password) if password else ""
            if smtp_port == 465:
                server = smtplib.SMTP_SSL(smtp_host_str, smtp_port)
            else:
                server = smtplib.SMTP(smtp_host_str, smtp_port)
                if smtp_port == 587:
                    server.starttls()
            
            server.login(username_str, password_str)
            server.sendmail(username_str, str(to_addr) if to_addr else "", msg.as_string())
            server.quit()
            
            return {
                "success": True,
                "to": to_addr,
                "subject": subject
            }
            
        except Exception as e:
            return {"error": f"发送邮件失败: {e}"}
    
    async def _search_emails(self, kwargs: Dict[str, Any]) -> Dict[str, Any]:
        """搜索邮件"""
        imap_host = kwargs.get("imap_host") or "" or ""
        imap_port = kwargs.get("imap_port", 993)
        username = kwargs.get("username") or ""
        password = kwargs.get("password") or ""
        mailbox = kwargs.get("mailbox", "INBOX")
        search_query = kwargs.get("query", "ALL")
        limit = kwargs.get("limit", 10)
        
        if not all([imap_host, username, password]):
            return {"error": "缺少必要的IMAP配置参数"}
        
        try:
            if imap_port == 993:
                mail = imaplib.IMAP4_SSL(imap_host, imap_port)
            else:
                mail = imaplib.IMAP4(imap_host, imap_port)
            
            mail.login(username, password)
            mail.select(mailbox)
            
            status, messages = mail.search(None, search_query)
            
            if status != "OK":
                return {"error": "搜索邮件失败", "count": 0}
            
            email_ids = messages[0].split()
            
            # 限制数量
            email_ids = email_ids[-limit:] if len(email_ids) > limit else email_ids
            
            emails = []
            for email_id in email_ids:
                status, msg_data = mail.fetch(email_id, "(RFC822)")
                
                if status == "OK" and msg_data and len(msg_data) > 0:
                    msg_item = msg_data[0]
                    if msg_item and len(msg_item) > 1:
                        msg_bytes = msg_item[1]
                        if msg_bytes and isinstance(msg_bytes, bytes):
                            msg = email.message_from_bytes(msg_bytes)
                            email_data = self._parse_email(msg)
                            emails.append(email_data)
            
            mail.logout()
            
            return {
                "query": search_query,
                "found": len(emails),
                "emails": emails
            }
            
        except Exception as e:
            return {"error": f"搜索邮件失败: {e}"}
    
    async def _mark_as_read(self, kwargs: Dict[str, Any]) -> Dict[str, Any]:
        """标记邮件为已读"""
        imap_host = kwargs.get("imap_host") or "" or ""
        imap_port = kwargs.get("imap_port", 993)
        username = kwargs.get("username") or ""
        password = kwargs.get("password") or ""
        mailbox = kwargs.get("mailbox", "INBOX")
        email_id = kwargs.get("email_id") or ""
        
        if not all([imap_host, username, password, email_id]):
            return {"error": "缺少必要的IMAP配置参数"}
        
        try:
            if imap_port == 993:
                mail = imaplib.IMAP4_SSL(imap_host, imap_port)
            else:
                mail = imaplib.IMAP4(imap_host, imap_port)
            
            mail.login(username, password)
            mail.select(mailbox)
            
            # 标记为已读
            mail.store(email_id, "+FLAGS", "\\Seen")
            
            mail.logout()
            
            return {
                "success": True,
                "email_id": email_id,
                "marked_as": "read"
            }
            
        except Exception as e:
            return {"error": f"标记已读失败: {e}"}
    
    async def _list_folders(self, kwargs: Dict[str, Any]) -> Dict[str, Any]:
        """列出邮件夹"""
        imap_host = kwargs.get("imap_host") or "" or ""
        imap_port = kwargs.get("imap_port", 993)
        username = kwargs.get("username") or ""
        password = kwargs.get("password") or ""
        
        if not all([imap_host, username, password]):
            return {"error": "缺少必要的IMAP配置参数"}
        
        try:
            if imap_port == 993:
                mail = imaplib.IMAP4_SSL(imap_host, imap_port)
            else:
                mail = imaplib.IMAP4(imap_host, imap_port)
            
            mail.login(username, password)
            
            status, folders = mail.list()
            
            if status != "OK":
                return {"error": "获取邮件夹失败", "folders": []}
            
            folder_list = []
            for folder in folders:
                folder_str = ""
                if isinstance(folder, bytes):
                    folder_str = folder.decode('utf-8', errors='replace')
                elif isinstance(folder, str):
                    folder_str = folder
                # 解析邮件夹名称
                if folder_str and ' "/" ' in folder_str:
                    parts = folder_str.split(' "/" ')
                else:
                    parts = []
                if len(parts) > 1:
                    folder_name = parts[-1].strip('"')
                    folder_list.append(folder_name)
            
            mail.logout()
            
            return {
                "count": len(folder_list),
                "folders": folder_list
            }
            
        except Exception as e:
            return {"error": f"获取邮件夹失败: {e}"}
    
    def _parse_email(self, msg) -> Dict[str, Any]:
        """解析邮件内容"""
        subject = self._decode_header(msg.get("Subject", ""))
        sender = self._decode_header(msg.get("From", ""))
        to = self._decode_header(msg.get("To", ""))
        date = msg.get("Date", "")
        
        # 获取邮件正文
        body = ""
        html_body = ""
        
        if msg.is_multipart():
            for part in msg.walk():
                content_type = part.get_content_type()
                content_disposition = str(part.get("Content-Disposition"))
                
                if content_type == "text/plain" and "attachment" not in content_disposition:
                    try:
                        charset = part.get_content_charset() or 'utf-8'
                        body = part.get_payload(decode=True).decode(charset, errors='replace')
                    except:
                        body = part.get_payload(decode=True)
                elif content_type == "text/html" and "attachment" not in content_disposition:
                    try:
                        charset = part.get_content_charset() or 'utf-8'
                        html_body = part.get_payload(decode=True).decode(charset, errors='replace')
                    except:
                        html_body = part.get_payload(decode=True)
        else:
            try:
                charset = msg.get_content_charset() or 'utf-8'
                body = msg.get_payload(decode=True).decode(charset, errors='replace')
            except:
                body = str(msg.get_payload())
        
        return {
            "subject": subject,
            "from": sender,
            "to": to,
            "date": date,
            "body": body[:500] if body else "",  # 截取前500字符
            "html_body": html_body[:500] if html_body else "",
            "is_read": False
        }
    
    def _decode_header(self, header: str) -> str:
        """解码邮件头"""
        if not header:
            return ""
        
        decoded_parts = []
        try:
            parts = decode_header(header)
            for content, charset in parts:
                if isinstance(content, bytes):
                    charset = charset or 'utf-8'
                    try:
                        decoded_parts.append(content.decode(charset, errors='replace'))
                    except:
                        decoded_parts.append(content.decode('utf-8', errors='replace'))
                else:
                    decoded_parts.append(content)
        except:
            return header
        
        return ''.join(decoded_parts)


# 创建默认实例供注册表使用
email_hand = EmailHand()
