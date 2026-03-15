"""
Model Management API Routes - REST API for Model CRUD operations
"""
from fastapi import APIRouter, HTTPException, status
from typing import List, Optional
from pydantic import BaseModel, Field
from datetime import datetime

from src.services.model_service import (
    get_provider_service,
    get_model_service,
    get_fine_tune_service,
    get_training_service,
    get_model_switch_service
)

router = APIRouter(prefix="/api/v1/models", tags=["models"])


# ========== Data Models ==========

class ProviderCreate(BaseModel):
    """Create Model Provider request model"""
    name: str = Field(..., description="Provider name (unique key)")
    display_name: str = Field(..., description="Display name")
    description: Optional[str] = Field(None, description="Description")
    website: Optional[str] = Field(None, description="Website URL")
    api_type: str = Field(default="openai_compatible", description="API type")


class ProviderUpdate(BaseModel):
    """Update Provider request model"""
    name: Optional[str] = None
    display_name: Optional[str] = None
    description: Optional[str] = None
    website: Optional[str] = None
    api_type: Optional[str] = None
    status: Optional[str] = None


class ProviderResponse(BaseModel):
    """Provider response model"""
    id: str
    name: str
    display_name: str
    description: Optional[str]
    website: Optional[str]
    api_type: str
    status: str
    created_at: datetime
    updated_at: datetime


class ModelCreate(BaseModel):
    """Create Model request model"""
    provider_id: str = Field(..., description="Provider ID")
    name: str = Field(..., description="Model name (unique key)")
    display_name: str = Field(..., description="Display name")
    model_type: str = Field(default="llm", description="Model type: llm, embedding")
    description: Optional[str] = Field(None, description="Description")
    strengths: List[str] = Field(default_factory=list, description="Model strengths")
    context_length: int = Field(default=4096, description="Context length")
    supports_function_calling: bool = Field(default=False, description="Supports function calling")
    supports_vision: bool = Field(default=False, description="Supports vision")
    output_price: float = Field(default=0, description="Output price per 1M tokens")
    is_local: bool = Field(default=False, description="Is local model")
    ollama_model_name: Optional[str] = Field(None, description="Ollama model name")


class ModelUpdate(BaseModel):
    """Update Model request model"""
    name: Optional[str] = None
    display_name: Optional[str] = None
    model_type: Optional[str] = None
    description: Optional[str] = None
    strengths: Optional[List[str]] = None
    context_length: Optional[int] = None
    supports_function_calling: Optional[bool] = None
    supports_vision: Optional[bool] = None
    input_price: Optional[float] = None
    output_price: Optional[float] = None
    is_local: Optional[bool] = None
    ollama_model_name: Optional[str] = None
    status: Optional[str] = None


class ModelResponse(BaseModel):
    """Model response model"""
    id: str
    provider_id: str
    name: str
    display_name: str
    model_type: str
    description: Optional[str]
    strengths: List[str]
    context_length: int
    supports_function_calling: bool
    supports_vision: bool
    input_price: float
    output_price: float
    is_local: bool
    ollama_model_name: Optional[str]
    status: str
    is_default: bool
    provider_name: Optional[str] = None
    created_at: datetime
    updated_at: datetime


class FineTuneCreate(BaseModel):
    """Create Fine-tune Task request model"""
    name: str = Field(..., description="Task name")
    base_model_id: str = Field(..., description="Base model ID")
    description: Optional[str] = Field(None, description="Description")
    data_source_type: str = Field(default="file", description="Data source type: file, url")
    data_source_path: Optional[str] = Field(None, description="File path")
    data_source_url: Optional[str] = Field(None, description="Data URL")
    data_format: str = Field(default="jsonl", description="Data format: jsonl, csv, txt, json")
    epochs: int = Field(default=3, description="Training epochs")
    learning_rate: float = Field(default=0.0001, description="Learning rate")
    batch_size: int = Field(default=4, description="Batch size")


class FineTuneResponse(BaseModel):
    """Fine-tune task response model"""
    id: str
    name: str
    base_model_id: str
    base_model_name: Optional[str]
    description: Optional[str]
    data_source_type: str
    data_source_path: Optional[str]
    data_source_url: Optional[str]
    data_format: str
    epochs: int
    learning_rate: float
    batch_size: int
    status: str
    progress: int
    output_model_name: Optional[str]
    error_message: Optional[str]
    started_at: Optional[datetime]
    completed_at: Optional[datetime]
    created_at: datetime
    updated_at: datetime


class TrainingCreate(BaseModel):
    """Create Training Task request model"""
    name: str = Field(..., description="Task name")
    base_model_id: Optional[str] = Field(None, description="Base model ID (optional)")
    description: Optional[str] = Field(None, description="Description")
    model_type: str = Field(default="llm", description="Model type to train")
    training_data_type: str = Field(default="file", description="Data source type: file, url")
    data_source_path: Optional[str] = Field(None, description="File path")
    data_source_url: Optional[str] = Field(None, description="Data URL")
    data_format: str = Field(default="jsonl", description="Data format: jsonl, csv, txt, json")
    epochs: int = Field(default=10, description="Training epochs")
    learning_rate: float = Field(default=0.00001, description="Learning rate")
    batch_size: int = Field(default=8, description="Batch size")
    vocabulary_size: Optional[int] = Field(None, description="Vocabulary size")
    seq_length: int = Field(default=512, description="Sequence length")
    config: dict = Field(default_factory=dict, description="Additional config")


class TrainingResponse(BaseModel):
    """Training task response model"""
    id: str
    name: str
    base_model_id: Optional[str]
    base_model_name: Optional[str]
    description: Optional[str]
    model_type: str
    training_data_type: str
    data_source_path: Optional[str]
    data_source_url: Optional[str]
    data_format: str
    epochs: int
    learning_rate: float
    batch_size: int
    vocabulary_size: Optional[int]
    seq_length: int
    status: str
    progress: int
    current_epoch: int
    current_loss: Optional[float]
    output_model_name: Optional[str]
    error_message: Optional[str]
    started_at: Optional[datetime]
    completed_at: Optional[datetime]
    created_at: datetime
    updated_at: datetime


# ========== Model Provider Routes ==========

@router.post("/providers", response_model=ProviderResponse, status_code=status.HTTP_201_CREATED)
async def create_provider(provider: ProviderCreate):
    """Create a new model provider"""
    service = get_provider_service()
    try:
        result = service.create_provider(provider.model_dump())
        return result
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"创建模型供应商失败: {str(e)}"
        )


@router.get("/providers", response_model=List[ProviderResponse])
async def list_providers(status: Optional[str] = None):
    """Get model provider list"""
    service = get_provider_service()
    try:
        return service.list_providers(status)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"获取模型供应商列表失败: {str(e)}"
        )


@router.get("/providers/{provider_id}", response_model=ProviderResponse)
async def get_provider(provider_id: str):
    """Get provider details"""
    service = get_provider_service()
    provider = service.get_provider(provider_id)
    if not provider:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="模型供应商不存在"
        )
    return provider


@router.put("/providers/{provider_id}", response_model=ProviderResponse)
async def update_provider(provider_id: str, provider: ProviderUpdate):
    """Update provider"""
    service = get_provider_service()
    try:
        result = service.update_provider(provider_id, provider.model_dump(exclude_unset=True))
        if not result:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="模型供应商不存在"
            )
        return result
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"更新模型供应商失败: {str(e)}"
        )


@router.delete("/providers/{provider_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_provider(provider_id: str):
    """Delete provider"""
    service = get_provider_service()
    try:
        service.delete_provider(provider_id)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"删除模型供应商失败: {str(e)}"
        )


# ========== Model Routes ==========

@router.post("", response_model=ModelResponse, status_code=status.HTTP_201_CREATED)
async def create_model(model: ModelCreate):
    """Create a new model"""
    service = get_model_service()
    try:
        result = service.create_model(model.model_dump())
        return result
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"创建模型失败: {str(e)}"
        )


@router.get("", response_model=List[ModelResponse])
async def list_models(
    status: Optional[str] = None,
    provider_id: Optional[str] = None,
    model_type: Optional[str] = None
):
    """Get model list with filters"""
    service = get_model_service()
    try:
        return service.list_models(status, provider_id, model_type)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"获取模型列表失败: {str(e)}"
        )


@router.get("/marketplace", response_model=List[ModelResponse])
async def get_model_marketplace():
    """Get model marketplace - models with strengths and provider info"""
    service = get_model_service()
    try:
        return service.get_model_marketplace()
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"获取模型市场失败: {str(e)}"
        )


@router.get("/{model_id}", response_model=ModelResponse)
async def get_model(model_id: str):
    """Get model details"""
    service = get_model_service()
    model = service.get_model(model_id)
    if not model:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="模型不存在"
        )
    return model


@router.put("/{model_id}", response_model=ModelResponse)
async def update_model(model_id: str, model: ModelUpdate):
    """Update model"""
    service = get_model_service()
    try:
        result = service.update_model(model_id, model.model_dump(exclude_unset=True))
        if not result:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="模型不存在"
            )
        return result
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"更新模型失败: {str(e)}"
        )


@router.delete("/{model_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_model(model_id: str):
    """Delete model"""
    service = get_model_service()
    try:
        service.delete_model(model_id)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"删除模型失败: {str(e)}"
        )


@router.post("/{model_id}/set-default", response_model=ModelResponse)
async def set_default_model(model_id: str):
    """Set model as default for its provider"""
    service = get_model_service()
    try:
        success = service.set_default_model(model_id)
        if not success:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="模型不存在"
            )
        return service.get_model(model_id)
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"设置默认模型失败: {str(e)}"
        )


# ========== Model Switch Routes ==========

@router.get("/switch/current", response_model=ModelResponse)
async def get_current_model(model_type: str = "llm"):
    """Get current active model"""
    service = get_model_switch_service()
    try:
        model = service.get_current_model(model_type)
        if not model:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="没有可用的模型"
            )
        return model
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"获取当前模型失败: {str(e)}"
        )


@router.post("/switch/{model_id}", response_model=ModelResponse)
async def switch_model(model_id: str):
    """Switch to a different model"""
    service = get_model_switch_service()
    try:
        result = service.switch_model(model_id)
        if not result.get('success'):
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=result.get('error', '模型切换失败')
            )
        return result['model']
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"切换模型失败: {str(e)}"
        )


@router.get("/switch/available", response_model=List[ModelResponse])
async def list_available_models(model_type: str = "llm"):
    """List all available models for switching"""
    service = get_model_switch_service()
    try:
        return service.list_available_models(model_type)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"获取可用模型列表失败: {str(e)}"
        )


# ========== Fine-tune Routes ==========

@router.post("/fine-tune", response_model=FineTuneResponse, status_code=status.HTTP_201_CREATED)
async def create_fine_tune_task(task: FineTuneCreate):
    """Create a new fine-tuning task"""
    service = get_fine_tune_service()
    try:
        result = service.create_task(task.model_dump())
        return result
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"创建微调任务失败: {str(e)}"
        )


@router.get("/fine-tune", response_model=List[FineTuneResponse])
async def list_fine_tune_tasks(status: Optional[str] = None):
    """Get fine-tuning task list"""
    service = get_fine_tune_service()
    try:
        return service.list_tasks(status)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"获取微调任务列表失败: {str(e)}"
        )


@router.get("/fine-tune/{task_id}", response_model=FineTuneResponse)
async def get_fine_tune_task(task_id: str):
    """Get fine-tuning task details"""
    service = get_fine_tune_service()
    task = service.get_task(task_id)
    if not task:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="微调任务不存在"
        )
    return task


@router.delete("/fine-tune/{task_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_fine_tune_task(task_id: str):
    """Delete fine-tuning task"""
    service = get_fine_tune_service()
    try:
        service.delete_task(task_id)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"删除微调任务失败: {str(e)}"
        )


@router.post("/fine-tune/{task_id}/start")
async def start_fine_tune_task(task_id: str):
    """Start a fine-tuning task"""
    service = get_fine_tune_service()
    try:
        result = service.update_task_status(task_id, status='running', progress=0)
        if not result:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="微调任务不存在"
            )
        return result
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"启动微调任务失败: {str(e)}"
        )


# ========== Training Routes ==========

@router.post("/training", response_model=TrainingResponse, status_code=status.HTTP_201_CREATED)
async def create_training_task(task: TrainingCreate):
    """Create a new training task"""
    service = get_training_service()
    try:
        result = service.create_task(task.model_dump())
        return result
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"创建训练任务失败: {str(e)}"
        )


@router.get("/training", response_model=List[TrainingResponse])
async def list_training_tasks(status: Optional[str] = None):
    """Get training task list"""
    service = get_training_service()
    try:
        return service.list_tasks(status)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"获取训练任务列表失败: {str(e)}"
        )


@router.get("/training/{task_id}", response_model=TrainingResponse)
async def get_training_task(task_id: str):
    """Get training task details"""
    service = get_training_service()
    task = service.get_task(task_id)
    if not task:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="训练任务不存在"
        )
    return task


@router.delete("/training/{task_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_training_task(task_id: str):
    """Delete training task"""
    service = get_training_service()
    try:
        service.delete_task(task_id)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"删除训练任务失败: {str(e)}"
        )


@router.post("/training/{task_id}/start")
async def start_training_task(task_id: str):
    """Start a training task"""
    service = get_training_service()
    try:
        result = service.update_task_status(task_id, status='running', progress=0)
        if not result:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="训练任务不存在"
            )
        return result
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"启动训练任务失败: {str(e)}"
        )
