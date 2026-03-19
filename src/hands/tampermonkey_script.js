// ==UserScript==
// @name         RANGEN Browser Control
// @namespace    https://github.com/rangen/rangen
// @version      1.0
// @description  RANGEN 浏览器控制扩展 - 支持 Agent 自动化操作
// @author       RANGEN
// @match        *://*/*
// @grant        GM_xmlhttpRequest
// @grant        GM_setValue
// @grant        GM_getValue
// @grant        GM_addStyle
// @grant        GM_setClipboard
// @connect      localhost
// @connect      127.0.0.1
// @run-at       document-idle
// @noframes
// ==/UserScript==

(function() {
    'use strict';
    
    // 配置
    const CONFIG = {
        API_ENDPOINT: 'http://localhost:8080/browser',
        HEARTBEAT_INTERVAL: 5000,
        DEBUG: false
    };
    
    // 日志
    function log(...args) {
        if (CONFIG.DEBUG) {
            console.log('[RANGEN]', ...args);
        }
    }
    
    // 状态
    let isConnected = false;
    let sessionId = null;
    
    // 发送消息到 RANGEN
    function sendToRangen(action, data = {}) {
        return new Promise((resolve, reject) => {
            GM_xmlhttpRequest({
                method: 'POST',
                url: `${CONFIG.API_ENDPOINT}/action`,
                data: JSON.stringify({
                    session_id: sessionId,
                    action: action,
                    data: data,
                    url: window.location.href,
                    timestamp: Date.now()
                }),
                headers: {
                    'Content-Type': 'application/json'
                },
                onload: function(response) {
                    try {
                        resolve(JSON.parse(response.responseText));
                    } catch (e) {
                        resolve({ success: true, output: response.responseText });
                    }
                },
                onerror: function(error) {
                    reject(error);
                }
            });
        });
    }
    
    // 心跳
    function heartbeat() {
        if (!isConnected) return;
        
        sendToRangen('heartbeat', {
            url: window.location.href,
            title: document.title
        }).catch(() => {
            log('Heartbeat failed');
        });
    }
    
    // 监听消息
    window.addEventListener('message', function(event) {
        // 只接受来自扩展本身的消息
        if (event.source !== window) return;
        
        const data = event.data;
        if (!data || data.type !== 'RANGEN_COMMAND') return;
        
        log('Received command:', data.command);
        
        handleCommand(data.command, data.data);
    });
    
    // 处理命令
    async function handleCommand(command, data) {
        try {
            let result;
            
            switch (command) {
                case 'connect':
                    sessionId = data.session_id;
                    isConnected = true;
                    result = { success: true, session_id: sessionId };
                    setInterval(heartbeat, CONFIG.HEARTBEAT_INTERVAL);
                    break;
                    
                case 'disconnect':
                    isConnected = false;
                    sessionId = null;
                    result = { success: true };
                    break;
                    
                case 'get_content':
                    result = {
                        success: true,
                        output: {
                            url: window.location.href,
                            title: document.title,
                            html: document.documentElement.outerHTML,
                            text: document.body.innerText
                        }
                    };
                    break;
                    
                case 'click':
                    const clickTarget = data.selector ? 
                        document.querySelector(data.selector) : null;
                    if (clickTarget) {
                        clickTarget.click();
                        result = { success: true, output: 'Clicked' };
                    } else {
                        result = { success: false, error: 'Element not found' };
                    }
                    break;
                    
                case 'type':
                    const typeTarget = data.selector ? 
                        document.querySelector(data.selector) : null;
                    if (typeTarget) {
                        typeTarget.value = data.value;
                        typeTarget.dispatchEvent(new Event('input', { bubbles: true }));
                        result = { success: true, output: 'Typed' };
                    } else {
                        result = { success: false, error: 'Element not found' };
                    }
                    break;
                    
                case 'screenshot':
                    // 使用 html2canvas 或类似库
                    result = { 
                        success: true, 
                        output: 'Screenshot functionality requires additional library'
                    };
                    break;
                    
                case 'evaluate':
                    try {
                        const evalResult = eval(data.script);
                        result = { success: true, output: evalResult };
                    } catch (e) {
                        result = { success: false, error: e.message };
                    }
                    break;
                    
                default:
                    result = { success: false, error: 'Unknown command' };
            }
            
            // 发送结果
            window.postMessage({
                type: 'RANGEN_RESULT',
                command: command,
                result: result
            }, '*');
            
        } catch (e) {
            log('Command error:', e);
            window.postMessage({
                type: 'RANGEN_RESULT',
                command: command,
                result: { success: false, error: e.message }
            }, '*');
        }
    }
    
    // 初始化
    log('RANGEN Browser Control initialized');
    
    // 添加全局 API
    window.RANGEN_BROWSER = {
        send: sendToRangen,
        config: CONFIG
    };
    
})();
