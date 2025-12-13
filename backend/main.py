# Notify Hub - A lightweight notification routing service.
# Copyright (C) 2025 Notify Hub Authors
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU Affero General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU Affero General Public License for more details.
#
# You should have received a copy of the GNU Affero General Public License
# along with this program.  If not, see <https://www.gnu.org/licenses/>.

from fastapi import FastAPI, Depends, HTTPException, Header, status, Request
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.gzip import GZipMiddleware
from fastapi.responses import FileResponse, Response
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from typing import List, Optional
import models
from database import engine, get_db
from pydantic import BaseModel
import secrets
from contextlib import asynccontextmanager
import os
from datetime import datetime, timedelta
from jose import JWTError, jwt
from passlib.context import CryptContext

# Auth Config
SECRET_KEY = os.getenv("SECRET_KEY", "your-secret-key-should-be-changed")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 60 * 24 # 1 day

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="api/login")

# Lifecycle
@asynccontextmanager
async def lifespan(app: FastAPI):
    # Establish DB connection and create tables
    async with engine.begin() as conn:
        await conn.run_sync(models.Base.metadata.create_all)
    yield

app = FastAPI(title="Notify Hub API", lifespan=lifespan)

# CORS & Gzip
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], 
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
app.add_middleware(GZipMiddleware, minimum_size=1000)

# Serves Static Files (SPA Support)
import mimetypes
mimetypes.init()
mimetypes.add_type("application/javascript", ".js")
mimetypes.add_type("text/css", ".css")

static_dir = "static"

# Schemas
class ProjectCreate(BaseModel):
    name: str

class ProjectResponse(BaseModel):
    id: int
    name: str
    api_key: str
    created_at: str 

class MessageCreate(BaseModel):
    project_name: str 
    title: Optional[str] = None
    content: str
    level: str = "info"

class MessageResponse(BaseModel):
    id: int
    project_name: str
    title: Optional[str]
    content: str
    level: str
    created_at: str
    is_read: bool

class Token(BaseModel):
    access_token: str
    token_type: str

# Helpers
def create_access_token(data: dict):
    to_encode = data.copy()
    expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

async def get_current_user(token: str = Depends(oauth2_scheme)):
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username: str = payload.get("sub")
        if username is None:
            raise credentials_exception
    except JWTError:
        raise credentials_exception
    return username

# Lifecycle
@asynccontextmanager
async def lifespan(app: FastAPI):
    # Establish DB connection and create tables
    async with engine.begin() as conn:
        await conn.run_sync(models.Base.metadata.create_all)
    yield

app = FastAPI(title="Notify Hub API", lifespan=lifespan)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], # In production, restrict this
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Routes

@app.post("/api/login", response_model=Token)
async def login(form_data: OAuth2PasswordRequestForm = Depends()):
    # Simple env var check
    web_username = os.getenv("WEB_USERNAME", "admin")
    web_password = os.getenv("WEB_PASSWORD", "admin")
    
    if form_data.username != web_username or form_data.password != web_password:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    access_token = create_access_token(data={"sub": form_data.username})
    return {"access_token": access_token, "token_type": "bearer"}

@app.post("/api/projects", response_model=ProjectResponse)
async def create_project(project: ProjectCreate, current_user: str = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    api_key = secrets.token_urlsafe(32)
    new_project = models.Project(name=project.name, api_key=api_key)
    db.add(new_project)
    await db.commit()
    await db.refresh(new_project)
    return ProjectResponse(
        id=new_project.id,
        name=new_project.name,
        api_key=new_project.api_key,
        created_at=new_project.created_at.isoformat()
    )

@app.get("/api/projects", response_model=List[ProjectResponse])
async def list_projects(current_user: str = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(models.Project))
    projects = result.scalars().all()
    return [
        ProjectResponse(
            id=p.id,
            name=p.name,
            api_key=p.api_key,
            created_at=p.created_at.isoformat()
        ) for p in projects
    ]

@app.delete("/api/projects/{project_id}")
async def delete_project(project_id: int, current_user: str = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    # Verify project exists
    project = await db.get(models.Project, project_id)
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    
    # Delete (Cascade should handle messages if configured, but let's be safe)
    # Since we don't have cascade configured in models explicitly for DB level, 
    # we rely on SQLAlchemy cascade or manual delete. 
    # For now, let's just delete the project. Messages will be orphaned or deleted depending on DB setup.
    await db.delete(project)
    await db.commit()
    return {"status": "success", "message": "Project deleted"}

@app.post("/api/notify")
async def create_notification(
    message: MessageCreate, 
    x_project_key: str = Header(..., alias="X-Project-Key"),
    db: AsyncSession = Depends(get_db)
):
    # 1. Global Auth Check
    global_notify_key = os.getenv("NOTIFY_KEY")
    if x_project_key != global_notify_key:
        raise HTTPException(status_code=403, detail="Invalid Global Project Key")
    
    # 2. Find or Create Project by Name
    stmt = select(models.Project).where(models.Project.name == message.project_name)
    result = await db.execute(stmt)
    project = result.scalar_one_or_none()
    
    if not project:
        # Create new project
        dummy_api_key = secrets.token_urlsafe(32)
        new_project = models.Project(name=message.project_name, api_key=dummy_api_key)
        db.add(new_project)
        try:
            await db.commit()
            await db.refresh(new_project)
            project = new_project
        except Exception as e:
            await db.rollback()
            raise HTTPException(status_code=500, detail=f"Failed to create project: {str(e)}")

    # 3. Save Message
    new_message = models.Message(
        project_id=project.id,
        title=message.title,
        content=message.content,
        level=message.level
    )
    db.add(new_message)
    await db.commit()
    return {"status": "success", "message_id": new_message.id, "project": project.name}

@app.get("/api/messages", response_model=List[MessageResponse])
async def get_messages(
    limit: int = 50, 
    skip: int = 0, 
    level: Optional[str] = None,
    project_id: Optional[int] = None,
    search: Optional[str] = None,
    start_date: Optional[datetime] = None,
    end_date: Optional[datetime] = None,
    current_user: str = Depends(get_current_user), 
    db: AsyncSession = Depends(get_db)
):
    # Default filter: is_deleted = False
    stmt = select(models.Message, models.Project).join(models.Project).where(models.Message.is_deleted == False).order_by(models.Message.created_at.desc())
    
    if level and level != 'all':
        stmt = stmt.where(models.Message.level == level)
    if project_id and project_id != 0: # 0 or None means all
        stmt = stmt.where(models.Message.project_id == project_id)
    if search:
        search_term = f"%{search}%"
        stmt = stmt.where((models.Message.title.ilike(search_term)) | (models.Message.content.ilike(search_term)))
    
    if start_date:
        stmt = stmt.where(models.Message.created_at >= start_date)
    if end_date:
        stmt = stmt.where(models.Message.created_at <= end_date)
        
    stmt = stmt.offset(skip).limit(limit)
    
    result = await db.execute(stmt)
    
    messages_data = []
    for msg, proj in result:
        messages_data.append(MessageResponse(
            id=msg.id,
            project_name=proj.name,
            title=msg.title,
            content=msg.content,
            level=msg.level,
            created_at=msg.created_at.isoformat(),
            is_read=msg.is_read
        ))
    return messages_data

@app.delete("/api/messages/{message_id}")
async def delete_message(message_id: int, current_user: str = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    msg = await db.get(models.Message, message_id)
    if not msg:
        raise HTTPException(status_code=404, detail="Message not found")
    
    msg.is_deleted = True
    await db.commit()
    return {"status": "success", "message": "Message soft deleted"}

@app.delete("/api/system/purge")
async def purge_deleted_messages(current_user: str = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    # Hard delete all is_deleted=True
    from sqlalchemy import delete
    stmt = delete(models.Message).where(models.Message.is_deleted == True)
    result = await db.execute(stmt)
    await db.commit()
    return {"status": "success", "deleted_count": result.rowcount}

@app.get("/{full_path:path}")
async def catch_all(full_path: str, request: Request = None): # Add request parameter
    # 1. SPECIAL HANDLING FOR ASSETS
    if full_path.startswith("assets/") or full_path == "vite.svg":
        file_disk_path = os.path.join(static_dir, full_path) if full_path != "vite.svg" else os.path.join(static_dir, "vite.svg")
        
        # Check for pre-compressed file (.br) - Prioritize Brotli
        br_path = file_disk_path + ".br"
        gzip_path = file_disk_path + ".gz"
        accept_encoding = request.headers.get("accept-encoding", "") if request else ""
        
        if "br" in accept_encoding and os.path.exists(br_path) and os.path.isfile(br_path):
             mime_type, _ = mimetypes.guess_type(file_disk_path) 
             if full_path.endswith(".js"): mime_type = "application/javascript"
             elif full_path.endswith(".css"): mime_type = "text/css"
             return FileResponse(br_path, media_type=mime_type, headers={"Content-Encoding": "br"})

        if "gzip" in accept_encoding and os.path.exists(gzip_path) and os.path.isfile(gzip_path):
             mime_type, _ = mimetypes.guess_type(file_disk_path)
             if full_path.endswith(".js"): mime_type = "application/javascript"
             elif full_path.endswith(".css"): mime_type = "text/css"
             return FileResponse(gzip_path, media_type=mime_type, headers={"Content-Encoding": "gzip"})

        if os.path.exists(file_disk_path) and os.path.isfile(file_disk_path):
             mime_type, _ = mimetypes.guess_type(file_disk_path)
             if full_path.endswith(".js"): 
                 mime_type = "application/javascript"
             elif full_path.endswith(".css"):
                 mime_type = "text/css"
             return FileResponse(file_disk_path, media_type=mime_type)
        else:
             return Response(status_code=404)

    # 2. SPA Fallback (Return index.html)
    index_path = f"{static_dir}/index.html"
    if os.path.exists(index_path):
        return FileResponse(index_path)
    
    return {"message": "Notify Hub API is running. (Frontend not built/found in static/)"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
