import os
import uuid
import json
import asyncio
import subprocess
import paramiko
from datetime import datetime, timezone
from typing import List, Optional, Dict, Any
from dotenv import load_dotenv

from fastapi import FastAPI, WebSocket, WebSocketDisconnect, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from motor.motor_asyncio import AsyncIOMotorClient

# Load environment variables
load_dotenv()

# Import LLM integration
from emergentintegrations.llm.chat import LlmChat, UserMessage

app = FastAPI(title="JARVIS Assistant API")

# CORS configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# MongoDB setup
MONGO_URL = os.environ.get('MONGO_URL', 'mongodb://localhost:27017')
client = AsyncIOMotorClient(MONGO_URL)
db = client.jarvis_db

# Pydantic models
class ChatMessage(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    session_id: str
    message: str
    sender: str  # 'user' or 'jarvis'
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    message_type: str = "text"  # 'text', 'command_proposal', 'command_result'

class Command(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    session_id: str
    command: str
    description: str
    platform: str  # 'windows', 'linux'
    status: str = "pending"  # 'pending', 'approved', 'rejected', 'executed', 'failed'
    result: Optional[str] = None
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    approved_at: Optional[datetime] = None
    executed_at: Optional[datetime] = None

class SystemInfo(BaseModel):
    platform: str
    disk_usage: Dict[str, Any]
    memory_info: Dict[str, Any]
    cpu_info: Dict[str, Any]
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

# WebSocket connection manager
class ConnectionManager:
    def __init__(self):
        self.active_connections: List[WebSocket] = []

    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.append(websocket)

    def disconnect(self, websocket: WebSocket):
        self.active_connections.remove(websocket)

    async def send_personal_message(self, message: str, websocket: WebSocket):
        await websocket.send_text(message)

    async def broadcast(self, message: str):
        for connection in self.active_connections:
            await connection.send_text(message)

manager = ConnectionManager()

# Gemini AI integration
GEMINI_API_KEY = "AIzaSyCJM0oyamxY6xpOBiGyESMG1Oncw57qI94"

class JarvisAI:
    def __init__(self):
        self.chat = None
        
    async def initialize_chat(self, session_id: str):
        system_message = """You are JARVIS, Tony Stark's AI assistant from Iron Man. You are intelligent, professional, and sophisticated. 
        
        Your capabilities include:
        - Analyzing and proposing system commands
        - Providing detailed technical information
        - Managing computer operations with user approval
        - SSH access to remote servers
        - File analysis and system monitoring
        
        Always be professional, concise, and helpful. When proposing commands, explain what they do and why they're needed.
        Respond in a manner fitting for an advanced AI assistant."""
        
        self.chat = LlmChat(
            api_key=GEMINI_API_KEY,
            session_id=session_id,
            system_message=system_message
        ).with_model("gemini", "gemini-2.5-pro")
    
    async def get_response(self, user_message: str, context: Dict = None) -> str:
        if not self.chat:
            raise Exception("Chat not initialized")
        
        # Add context if provided
        if context:
            enhanced_message = f"Context: {json.dumps(context)}\n\nUser: {user_message}"
        else:
            enhanced_message = user_message
            
        message = UserMessage(text=enhanced_message)
        response = await self.chat.send_message(message)
        return response

jarvis_ai = JarvisAI()

# Command execution functions
async def execute_windows_command(command: str) -> Dict[str, Any]:
    """Execute Windows command safely"""
    try:
        result = subprocess.run(
            command,
            shell=True,
            capture_output=True,
            text=True,
            timeout=30
        )
        return {
            "success": True,
            "output": result.stdout,
            "error": result.stderr,
            "return_code": result.returncode
        }
    except subprocess.TimeoutExpired:
        return {
            "success": False,
            "output": "",
            "error": "Command timed out after 30 seconds",
            "return_code": -1
        }
    except Exception as e:
        return {
            "success": False,
            "output": "",
            "error": str(e),
            "return_code": -1
        }

async def execute_ssh_command(host: str, username: str, password: str, command: str) -> Dict[str, Any]:
    """Execute command on remote server via SSH"""
    try:
        ssh = paramiko.SSHClient()
        ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        ssh.connect(host, username=username, password=password, timeout=10)
        
        stdin, stdout, stderr = ssh.exec_command(command, timeout=30)
        
        output = stdout.read().decode()
        error = stderr.read().decode()
        return_code = stdout.channel.recv_exit_status()
        
        ssh.close()
        
        return {
            "success": return_code == 0,
            "output": output,
            "error": error,
            "return_code": return_code
        }
    except Exception as e:
        return {
            "success": False,
            "output": "",
            "error": str(e),
            "return_code": -1
        }

async def get_system_info() -> SystemInfo:
    """Get current system information"""
    try:
        # Disk usage
        disk_cmd = "wmic logicaldisk get size,freespace,caption"
        disk_result = await execute_windows_command(disk_cmd)
        
        # Memory info
        memory_cmd = "wmic OS get TotalVisibleMemorySize,FreePhysicalMemory /value"
        memory_result = await execute_windows_command(memory_cmd)
        
        # CPU info
        cpu_cmd = "wmic cpu get name,NumberOfCores,MaxClockSpeed /value"
        cpu_result = await execute_windows_command(cpu_cmd)
        
        return SystemInfo(
            platform="windows",
            disk_usage={"raw_output": disk_result.get("output", "")},
            memory_info={"raw_output": memory_result.get("output", "")},
            cpu_info={"raw_output": cpu_result.get("output", "")}
        )
    except Exception as e:
        return SystemInfo(
            platform="windows",
            disk_usage={"error": str(e)},
            memory_info={"error": str(e)},
            cpu_info={"error": str(e)}
        )

# API Routes
@app.get("/api/health")
async def health_check():
    return {"status": "online", "service": "JARVIS"}

@app.get("/api/system-info")
async def get_system_info_endpoint():
    """Get current system information"""
    info = await get_system_info()
    return info

@app.post("/api/commands/{command_id}/approve")
async def approve_command(command_id: str):
    """Approve a pending command for execution"""
    command = await db.commands.find_one({"id": command_id})
    if not command:
        raise HTTPException(status_code=404, detail="Command not found")
    
    if command["status"] != "pending":
        raise HTTPException(status_code=400, detail="Command is not pending approval")
    
    # Update command status
    await db.commands.update_one(
        {"id": command_id},
        {
            "$set": {
                "status": "approved",
                "approved_at": datetime.now(timezone.utc).isoformat()
            }
        }
    )
    
    # Execute the command
    if command["platform"] == "windows":
        result = await execute_windows_command(command["command"])
    else:
        # For SSH commands, you'd need to provide host, username, password
        result = {"success": False, "error": "SSH execution not implemented in this endpoint"}
    
    # Update command with execution result
    await db.commands.update_one(
        {"id": command_id},
        {
            "$set": {
                "status": "executed" if result["success"] else "failed",
                "result": json.dumps(result),
                "executed_at": datetime.now(timezone.utc).isoformat()
            }
        }
    )
    
    return {"command_id": command_id, "result": result}

@app.post("/api/commands/{command_id}/reject")
async def reject_command(command_id: str):
    """Reject a pending command"""
    await db.commands.update_one(
        {"id": command_id},
        {"$set": {"status": "rejected"}}
    )
    return {"command_id": command_id, "status": "rejected"}

@app.websocket("/api/ws/{session_id}")
async def websocket_endpoint(websocket: WebSocket, session_id: str):
    await manager.connect(websocket)
    
    # Initialize JARVIS AI for this session
    await jarvis_ai.initialize_chat(session_id)
    
    # Send welcome message
    welcome_msg = {
        "type": "message",
        "data": {
            "id": str(uuid.uuid4()),
            "session_id": session_id,
            "message": "Good day, sir. JARVIS is online and ready to assist you.",
            "sender": "jarvis",
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "message_type": "text"
        }
    }
    await manager.send_personal_message(json.dumps(welcome_msg), websocket)
    
    try:
        while True:
            # Receive message from client
            data = await websocket.receive_text()
            message_data = json.loads(data)
            
            # Save user message to database
            user_message = ChatMessage(
                session_id=session_id,
                message=message_data["message"],
                sender="user"
            )
            user_message_data = user_message.dict()
            user_message_data["timestamp"] = user_message_data["timestamp"].isoformat()
            await db.messages.insert_one(user_message_data)
            
            # Get AI response
            try:
                # Add system context if needed
                context = {
                    "platform": "windows",
                    "capabilities": ["system_commands", "ssh_access", "file_analysis"]
                }
                
                ai_response = await jarvis_ai.get_response(message_data["message"], context)
                
                # Check if the response suggests a command
                user_msg_lower = message_data["message"].lower()
                ai_response_lower = ai_response.lower()
                
                # Check for folder creation command in user message
                folder_creation_phrases = [
                    'klasör oluştur',
                    'yeni klasör yap',
                    'folder oluştur',
                    'create folder',
                    'make directory',
                    'mkdir'
                ]
                
                # Default command indicators
                command_indicators = [
                    ("disk space" in user_msg_lower or "disk" in user_msg_lower, "wmic logicaldisk get size,freespace,caption", "Get disk space information for all drives"),
                    ("memory" in user_msg_lower or "ram" in user_msg_lower, "wmic OS get TotalVisibleMemorySize,FreePhysicalMemory /value", "Get system memory information"),
                    ("start valorant" in user_msg_lower, 'powershell "Get-ChildItem -Path C:\\ -Recurse -Name valorant.exe -ErrorAction SilentlyContinue | Select-Object -First 1"', "Search for Valorant executable and start it"),
                    (any(phrase in user_msg_lower for phrase in folder_creation_phrases), None, "Create a new folder"),
                    ("wmic" in ai_response_lower or "command" in ai_response_lower, "echo 'Command detected'", "Execute proposed system command")
                ]
                
                command_detected = False
                suggested_command = None
                command_description = None
                folder_name = None
                
                # Check for folder creation first
                if any(phrase in user_msg_lower for phrase in folder_creation_phrases):
                    # Extract folder name from the message
                    import re
                    folder_match = re.search(r'(["\'])(.*?)\1', message_data["message"])
                    if folder_match:
                        folder_name = folder_match.group(2)
                    else:
                        # Try to extract folder name without quotes
                        words = message_data["message"].split()
                        for i, word in enumerate(words):
                            if word.lower() in ["oluştur", "oluşturma", "yap", "create", "make"] and i + 1 < len(words):
                                folder_name = words[i + 1]
                                break
                    
                    if folder_name:
                        # Create full path on desktop
                        desktop_path = os.path.join(os.path.expanduser('~'), 'Desktop')
                        folder_path = os.path.join(desktop_path, folder_name)
                        
                        # Create the folder
                        try:
                            os.makedirs(folder_path, exist_ok=True)
                            command_detected = True
                            command_description = f"Klasör oluşturuldu: {folder_path}"
                            
                            # Send success message
                            success_msg = {
                                "type": "message",
                                "data": {
                                    "id": str(uuid.uuid4()),
                                    "session_id": session_id,
                                    "message": f"Klasör başarıyla oluşturuldu: {folder_path}",
                                    "sender": "jarvis",
                                    "timestamp": datetime.now(timezone.utc).isoformat(),
                                    "message_type": "text"
                                }
                            }
                            await manager.send_personal_message(json.dumps(success_msg), websocket)
                            continue  # Skip the rest of the loop since we handled this case
                            
                        except Exception as e:
                            error_msg = {
                                "type": "message",
                                "data": {
                                    "id": str(uuid.uuid4()),
                                    "session_id": session_id,
                                    "message": f"Klasör oluşturulurken hata oluştu: {str(e)}",
                                    "sender": "jarvis",
                                    "timestamp": datetime.now(timezone.utc).isoformat(),
                                    "message_type": "error"
                                }
                            }
                            await manager.send_personal_message(json.dumps(error_msg), websocket)
                            continue
                
                # Check other command indicators if no folder creation was detected
                if not command_detected:
                    for condition, cmd, desc in command_indicators:
                        if condition and cmd:  # Only process if cmd is not None
                            suggested_command = cmd
                            command_description = desc
                            command_detected = True
                            break
                
                if command_detected:
                    # This is a command proposal
                    message_type = "command_proposal"
                    
                    # Save command proposal
                    command = Command(
                        session_id=session_id,
                        command=suggested_command,
                        description=command_description,
                        platform="windows"
                    )
                    command_data = command.dict()
                    command_data["timestamp"] = command_data["timestamp"].isoformat()
                    await db.commands.insert_one(command_data)
                    
                    # Enhance AI response with command details
                    ai_response = f"{ai_response}\n\n**Proposed Command:**\n`{suggested_command}`\n\n**Description:** {command_description}\n\n**Command ID:** {command.id}"
                
                else:
                    message_type = "text"
                
                # Save AI response to database
                jarvis_message = ChatMessage(
                    session_id=session_id,
                    message=ai_response,
                    sender="jarvis",
                    message_type=message_type
                )
                jarvis_message_data = jarvis_message.dict()
                jarvis_message_data["timestamp"] = jarvis_message_data["timestamp"].isoformat()
                await db.messages.insert_one(jarvis_message_data)
                
                # Send response to client
                response_data = jarvis_message.dict()
                response_data["timestamp"] = response_data["timestamp"].isoformat()
                response_msg = {
                    "type": "message",
                    "data": response_data
                }
                await manager.send_personal_message(json.dumps(response_msg), websocket)
                
            except Exception as e:
                error_message = ChatMessage(
                    session_id=session_id,
                    message=f"I apologize, but I encountered an error: {str(e)}",
                    sender="jarvis",
                    message_type="error"
                )
                error_message_data = error_message.dict()
                error_message_data["timestamp"] = error_message_data["timestamp"].isoformat()
                await db.messages.insert_one(error_message_data)
                
                error_data = error_message.dict()
                error_data["timestamp"] = error_data["timestamp"].isoformat()
                error_msg = {
                    "type": "message",
                    "data": error_data
                }
                await manager.send_personal_message(json.dumps(error_msg), websocket)
                
    except WebSocketDisconnect:
        manager.disconnect(websocket)

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="localhost", port=8001, log_level="info")