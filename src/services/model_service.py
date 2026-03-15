"""
Model Service - Business logic for Model management (Marketplace, Fine-tuning, Training)
"""
import uuid
import json
import os
from typing import List, Dict, Any, Optional
from datetime import datetime
from src.services.database import get_database
from src.services.logging_service import get_logger

logger = get_logger(__name__)


class ModelProviderService:
    """Model Provider business logic service"""
    
    def __init__(self):
        self.db = get_database()
    
    def _generate_id(self) -> str:
        """Generate unique ID"""
        return f"provider_{uuid.uuid4().hex[:12]}"
    
    def create_provider(self, provider_data: Dict[str, Any]) -> Dict[str, Any]:
        """Create a new model provider"""
        provider_id = self._generate_id()
        
        data = {
            'id': provider_id,
            'name': provider_data.get('name'),
            'display_name': provider_data.get('display_name'),
            'description': provider_data.get('description'),
            'website': provider_data.get('website'),
            'api_type': provider_data.get('api_type', 'openai_compatible'),
            'status': provider_data.get('status', 'active')
        }
        
        conn = self.db.get_connection()
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO model_providers (id, name, display_name, description, website, api_type, status)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (data['id'], data['name'], data['display_name'], data['description'], 
              data['website'], data['api_type'], data['status']))
        conn.commit()
        
        logger.info(f"Model provider created: {provider_id} - {data['display_name']}")
        return self.get_provider(provider_id)
    
    def get_provider(self, provider_id: str) -> Optional[Dict[str, Any]]:
        """Get provider details"""
        conn = self.db.get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM model_providers WHERE id = ?", (provider_id,))
        row = cursor.fetchone()
        
        if not row:
            return None
        
        return dict(row)
    
    def list_providers(self, status: Optional[str] = None) -> List[Dict[str, Any]]:
        """Get provider list"""
        conn = self.db.get_connection()
        cursor = conn.cursor()
        
        if status:
            cursor.execute("SELECT * FROM model_providers WHERE status = ? ORDER BY display_name", (status,))
        else:
            cursor.execute("SELECT * FROM model_providers ORDER BY display_name")
        
        return [dict(row) for row in cursor.fetchall()]
    
    def update_provider(self, provider_id: str, updates: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Update provider"""
        conn = self.db.get_connection()
        cursor = conn.cursor()
        
        # Build update query dynamically
        fields = []
        values = []
        for key in ['name', 'display_name', 'description', 'website', 'api_type', 'status']:
            if key in updates:
                fields.append(f"{key} = ?")
                values.append(updates[key])
        
        if not fields:
            return self.get_provider(provider_id)
        
        fields.append("updated_at = ?")
        values.append(datetime.now().isoformat())
        values.append(provider_id)
        
        cursor.execute(f"""
            UPDATE model_providers 
            SET {', '.join(fields)} 
            WHERE id = ?
        """, values)
        conn.commit()
        
        logger.info(f"Model provider updated: {provider_id}")
        return self.get_provider(provider_id)
    
    def delete_provider(self, provider_id: str) -> bool:
        """Delete provider"""
        conn = self.db.get_connection()
        cursor = conn.cursor()
        cursor.execute("DELETE FROM model_providers WHERE id = ?", (provider_id,))
        conn.commit()
        
        logger.info(f"Model provider deleted: {provider_id}")
        return True


class ModelManagementService:
    """Model Management business logic service"""
    
    def __init__(self):
        self.db = get_database()
    
    def _generate_id(self) -> str:
        """Generate unique ID"""
        return f"model_{uuid.uuid4().hex[:12]}"
    
    def create_model(self, model_data: Dict[str, Any]) -> Dict[str, Any]:
        """Create a new model"""
        model_id = self._generate_id()
        
        # Handle strengths as JSON string
        strengths = model_data.get('strengths')
        if isinstance(strengths, list):
            strengths = json.dumps(strengths, ensure_ascii=False)
        
        data = {
            'id': model_id,
            'provider_id': model_data.get('provider_id'),
            'name': model_data.get('name'),
            'display_name': model_data.get('display_name'),
            'model_type': model_data.get('model_type', 'llm'),
            'description': model_data.get('description'),
            'strengths': strengths,
            'context_length': model_data.get('context_length', 4096),
            'supports_function_calling': 1 if model_data.get('supports_function_calling') else 0,
            'supports_vision': 1 if model_data.get('supports_vision') else 0,
            'input_price': model_data.get('input_price', 0),
            'output_price': model_data.get('output_price', 0),
            'is_local': 1 if model_data.get('is_local') else 0,
            'ollama_model_name': model_data.get('ollama_model_name'),
            'status': model_data.get('status', 'active'),
            'is_default': 1 if model_data.get('is_default') else 0
        }
        
        conn = self.db.get_connection()
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO models (id, provider_id, name, display_name, model_type, description, 
                              strengths, context_length, supports_function_calling, supports_vision,
                              input_price, output_price, is_local, ollama_model_name, status, is_default)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (data['id'], data['provider_id'], data['name'], data['display_name'], data['model_type'],
              data['description'], data['strengths'], data['context_length'], data['supports_function_calling'],
              data['supports_vision'], data['input_price'], data['output_price'], data['is_local'],
              data['ollama_model_name'], data['status'], data['is_default']))
        conn.commit()
        
        logger.info(f"Model created: {model_id} - {data['display_name']}")
        return self.get_model(model_id)
    
    def get_model(self, model_id: str) -> Optional[Dict[str, Any]]:
        """Get model details"""
        conn = self.db.get_connection()
        cursor = conn.cursor()
        cursor.execute("""
            SELECT m.*, p.display_name as provider_name 
            FROM models m 
            LEFT JOIN model_providers p ON m.provider_id = p.id 
            WHERE m.id = ?
        """, (model_id,))
        row = cursor.fetchone()
        
        if not row:
            return None
        
        result = dict(row)
        # Parse strengths JSON
        if result.get('strengths'):
            try:
                result['strengths'] = json.loads(result['strengths'])
            except:
                pass
        return result
    
    def list_models(self, status: Optional[str] = None, provider_id: Optional[str] = None, 
                   model_type: Optional[str] = None) -> List[Dict[str, Any]]:
        """Get model list with filters"""
        conn = self.db.get_connection()
        cursor = conn.cursor()
        
        query = """
            SELECT m.*, p.display_name as provider_name 
            FROM models m 
            LEFT JOIN model_providers p ON m.provider_id = p.id 
            WHERE 1=1
        """
        params = []
        
        if status:
            query += " AND m.status = ?"
            params.append(status)
        if provider_id:
            query += " AND m.provider_id = ?"
            params.append(provider_id)
        if model_type:
            query += " AND m.model_type = ?"
            params.append(model_type)
        
        query += " ORDER BY p.display_name, m.display_name"
        
        cursor.execute(query, params)
        results = []
        for row in cursor.fetchall():
            result = dict(row)
            if result.get('strengths'):
                try:
                    result['strengths'] = json.loads(result['strengths'])
                except:
                    pass
            results.append(result)
        
        return results
    
    def get_model_marketplace(self) -> List[Dict[str, Any]]:
        """Get model marketplace - models with provider info and strengths"""
        conn = self.db.get_connection()
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT m.id, m.name, m.display_name, m.model_type, m.description, 
                   m.strengths, m.context_length, m.supports_function_calling, 
                   m.supports_vision, m.input_price, m.output_price, m.is_local,
                   m.ollama_model_name, m.is_default, m.status,
                   p.id as provider_id, p.display_name as provider_name, p.name as provider_key
            FROM models m 
            LEFT JOIN model_providers p ON m.provider_id = p.id 
            WHERE m.status = 'active'
            ORDER BY p.display_name, m.is_default DESC, m.display_name
        """)
        
        results = []
        for row in cursor.fetchall():
            result = dict(row)
            if result.get('strengths'):
                try:
                    result['strengths'] = json.loads(result['strengths'])
                except:
                    pass
            results.append(result)
        
        return results
    
    def set_default_model(self, model_id: str) -> bool:
        """Set a model as default"""
        conn = self.db.get_connection()
        cursor = conn.cursor()
        
        # First, unset all defaults for this provider
        cursor.execute("""
            SELECT provider_id FROM models WHERE id = ?
        """, (model_id,))
        row = cursor.fetchone()
        if not row:
            return False
        
        provider_id = row['provider_id']
        
        # Unset all defaults for this provider
        cursor.execute("UPDATE models SET is_default = 0 WHERE provider_id = ?", (provider_id,))
        
        # Set the new default
        cursor.execute("UPDATE models SET is_default = 1 WHERE id = ?", (model_id,))
        conn.commit()
        
        logger.info(f"Default model set: {model_id}")
        return True
    
    def update_model(self, model_id: str, updates: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Update model"""
        conn = self.db.get_connection()
        cursor = conn.cursor()
        
        # Handle strengths as JSON string
        if 'strengths' in updates and isinstance(updates['strengths'], list):
            updates['strengths'] = json.dumps(updates['strengths'], ensure_ascii=False)
        
        # Build update query dynamically
        allowed_fields = ['name', 'display_name', 'model_type', 'description', 'strengths',
                        'context_length', 'supports_function_calling', 'supports_vision',
                        'input_price', 'output_price', 'is_local', 'ollama_model_name', 
                        'status', 'is_default']
        
        fields = []
        values = []
        for key in allowed_fields:
            if key in updates:
                if key in ['supports_function_calling', 'supports_vision', 'is_local', 'is_default']:
                    fields.append(f"{key} = ?")
                    values.append(1 if updates[key] else 0)
                else:
                    fields.append(f"{key} = ?")
                    values.append(updates[key])
        
        if not fields:
            return self.get_model(model_id)
        
        fields.append("updated_at = ?")
        values.append(datetime.now().isoformat())
        values.append(model_id)
        
        cursor.execute(f"""
            UPDATE models 
            SET {', '.join(fields)} 
            WHERE id = ?
        """, values)
        conn.commit()
        
        logger.info(f"Model updated: {model_id}")
        return self.get_model(model_id)
    
    def delete_model(self, model_id: str) -> bool:
        """Delete model"""
        conn = self.db.get_connection()
        cursor = conn.cursor()
        cursor.execute("DELETE FROM models WHERE id = ?", (model_id,))
        conn.commit()
        
        logger.info(f"Model deleted: {model_id}")
        return True


class FineTuneService:
    """Fine-tuning Task business logic service"""
    
    def __init__(self):
        self.db = get_database()
    
    def _generate_id(self) -> str:
        """Generate unique ID"""
        return f"finetune_{uuid.uuid4().hex[:12]}"
    
    def create_task(self, task_data: Dict[str, Any]) -> Dict[str, Any]:
        """Create a new fine-tuning task"""
        task_id = self._generate_id()
        
        data = {
            'id': task_id,
            'name': task_data.get('name'),
            'base_model_id': task_data.get('base_model_id'),
            'description': task_data.get('description'),
            'data_source_type': task_data.get('data_source_type', 'file'),
            'data_source_path': task_data.get('data_source_path'),
            'data_source_url': task_data.get('data_source_url'),
            'data_format': task_data.get('data_format', 'jsonl'),
            'epochs': task_data.get('epochs', 3),
            'learning_rate': task_data.get('learning_rate', 0.0001),
            'batch_size': task_data.get('batch_size', 4),
            'status': 'pending'
        }
        
        conn = self.db.get_connection()
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO fine_tune_tasks (id, name, base_model_id, description, 
                                        data_source_type, data_source_path, data_source_url,
                                        data_format, epochs, learning_rate, batch_size, status)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (data['id'], data['name'], data['base_model_id'], data['description'],
              data['data_source_type'], data['data_source_path'], data['data_source_url'],
              data['data_format'], data['epochs'], data['learning_rate'], 
              data['batch_size'], data['status']))
        conn.commit()
        
        logger.info(f"Fine-tune task created: {task_id} - {data['name']}")
        return self.get_task(task_id)
    
    def get_task(self, task_id: str) -> Optional[Dict[str, Any]]:
        """Get fine-tuning task details"""
        conn = self.db.get_connection()
        cursor = conn.cursor()
        cursor.execute("""
            SELECT t.*, m.display_name as base_model_name
            FROM fine_tune_tasks t
            LEFT JOIN models m ON t.base_model_id = m.id
            WHERE t.id = ?
        """, (task_id,))
        row = cursor.fetchone()
        
        return dict(row) if row else None
    
    def list_tasks(self, status: Optional[str] = None) -> List[Dict[str, Any]]:
        """Get fine-tuning task list"""
        conn = self.db.get_connection()
        cursor = conn.cursor()
        
        if status:
            cursor.execute("""
                SELECT t.*, m.display_name as base_model_name
                FROM fine_tune_tasks t
                LEFT JOIN models m ON t.base_model_id = m.id
                WHERE t.status = ?
                ORDER BY t.created_at DESC
            """, (status,))
        else:
            cursor.execute("""
                SELECT t.*, m.display_name as base_model_name
                FROM fine_tune_tasks t
                LEFT JOIN models m ON t.base_model_id = m.id
                ORDER BY t.created_at DESC
            """)
        
        return [dict(row) for row in cursor.fetchall()]
    
    def update_task_status(self, task_id: str, status: str, progress: int = None,
                          output_model_name: str = None, error_message: str = None) -> Optional[Dict[str, Any]]:
        """Update task status"""
        conn = self.db.get_connection()
        cursor = conn.cursor()
        
        updates = ["status = ?", "updated_at = ?"]
        values = [status, datetime.now().isoformat()]
        
        if progress is not None:
            updates.append("progress = ?")
            values.append(progress)
        
        if output_model_name is not None:
            updates.append("output_model_name = ?")
            values.append(output_model_name)
        
        if error_message is not None:
            updates.append("error_message = ?")
            values.append(error_message)
        
        if status == 'running' and not self.get_task(task_id).get('started_at'):
            updates.append("started_at = ?")
            values.append(datetime.now().isoformat())
        
        if status in ['completed', 'failed']:
            updates.append("completed_at = ?")
            values.append(datetime.now().isoformat())
        
        values.append(task_id)
        
        cursor.execute(f"""
            UPDATE fine_tune_tasks 
            SET {', '.join(updates)} 
            WHERE id = ?
        """, values)
        conn.commit()
        
        logger.info(f"Fine-tune task status updated: {task_id} - {status}")
        return self.get_task(task_id)
    
    def delete_task(self, task_id: str) -> bool:
        """Delete fine-tuning task"""
        conn = self.db.get_connection()
        cursor = conn.cursor()
        cursor.execute("DELETE FROM fine_tune_tasks WHERE id = ?", (task_id,))
        conn.commit()
        
        logger.info(f"Fine-tune task deleted: {task_id}")
        return True
    
    def validate_data_source(self, data_source_type: str, data_source_path: str = None, 
                           data_source_url: str = None, data_format: str = 'jsonl') -> Dict[str, Any]:
        """Validate data source for fine-tuning"""
        errors = []
        
        if data_source_type == 'file':
            if not data_source_path:
                errors.append("File path is required")
            elif not os.path.exists(data_source_path):
                errors.append(f"File not found: {data_source_path}")
            else:
                # Validate format
                valid_formats = ['jsonl', 'csv', 'txt', 'json']
                if data_format not in valid_formats:
                    errors.append(f"Invalid format. Supported: {valid_formats}")
        
        elif data_source_type == 'url':
            if not data_source_url:
                errors.append("URL is required")
        
        return {
            'valid': len(errors) == 0,
            'errors': errors
        }


class TrainingService:
    """Training Task business logic service"""
    
    def __init__(self):
        self.db = get_database()
    
    def _generate_id(self) -> str:
        """Generate unique ID"""
        return f"training_{uuid.uuid4().hex[:12]}"
    
    def create_task(self, task_data: Dict[str, Any]) -> Dict[str, Any]:
        """Create a new training task"""
        task_id = self._generate_id()
        
        data = {
            'id': task_id,
            'name': task_data.get('name'),
            'base_model_id': task_data.get('base_model_id'),
            'description': task_data.get('description'),
            'model_type': task_data.get('model_type', 'llm'),
            'training_data_type': task_data.get('training_data_type', 'file'),
            'data_source_path': task_data.get('data_source_path'),
            'data_source_url': task_data.get('data_source_url'),
            'data_format': task_data.get('data_format', 'jsonl'),
            'epochs': task_data.get('epochs', 10),
            'learning_rate': task_data.get('learning_rate', 0.00001),
            'batch_size': task_data.get('batch_size', 8),
            'vocabulary_size': task_data.get('vocabulary_size'),
            'seq_length': task_data.get('seq_length', 512),
            'status': 'pending',
            'config_json': json.dumps(task_data.get('config', {}), ensure_ascii=False)
        }
        
        conn = self.db.get_connection()
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO training_tasks (id, name, base_model_id, description, model_type,
                                        training_data_type, data_source_path, data_source_url,
                                        data_format, epochs, learning_rate, batch_size,
                                        vocabulary_size, seq_length, status, config_json)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (data['id'], data['name'], data['base_model_id'], data['description'],
              data['model_type'], data['training_data_type'], data['data_source_path'],
              data['data_source_url'], data['data_format'], data['epochs'], data['learning_rate'],
              data['batch_size'], data['vocabulary_size'], data['seq_length'], 
              data['status'], data['config_json']))
        conn.commit()
        
        logger.info(f"Training task created: {task_id} - {data['name']}")
        return self.get_task(task_id)
    
    def get_task(self, task_id: str) -> Optional[Dict[str, Any]]:
        """Get training task details"""
        conn = self.db.get_connection()
        cursor = conn.cursor()
        cursor.execute("""
            SELECT t.*, m.display_name as base_model_name
            FROM training_tasks t
            LEFT JOIN models m ON t.base_model_id = m.id
            WHERE t.id = ?
        """, (task_id,))
        row = cursor.fetchone()
        
        if not row:
            return None
        
        result = dict(row)
        if result.get('config_json'):
            try:
                result['config'] = json.loads(result['config_json'])
            except:
                pass
        return result
    
    def list_tasks(self, status: Optional[str] = None) -> List[Dict[str, Any]]:
        """Get training task list"""
        conn = self.db.get_connection()
        cursor = conn.cursor()
        
        if status:
            cursor.execute("""
                SELECT t.*, m.display_name as base_model_name
                FROM training_tasks t
                LEFT JOIN models m ON t.base_model_id = m.id
                WHERE t.status = ?
                ORDER BY t.created_at DESC
            """, (status,))
        else:
            cursor.execute("""
                SELECT t.*, m.display_name as base_model_name
                FROM training_tasks t
                LEFT JOIN models m ON t.base_model_id = m.id
                ORDER BY t.created_at DESC
            """)
        
        results = []
        for row in cursor.fetchall():
            result = dict(row)
            if result.get('config_json'):
                try:
                    result['config'] = json.loads(result['config_json'])
                except:
                    pass
            results.append(result)
        
        return results
    
    def update_task_status(self, task_id: str, status: str, progress: int = None,
                          current_epoch: int = None, current_loss: float = None,
                          output_model_name: str = None, error_message: str = None) -> Optional[Dict[str, Any]]:
        """Update task status"""
        conn = self.db.get_connection()
        cursor = conn.cursor()
        
        updates = ["status = ?", "updated_at = ?"]
        values = [status, datetime.now().isoformat()]
        
        if progress is not None:
            updates.append("progress = ?")
            values.append(progress)
        
        if current_epoch is not None:
            updates.append("current_epoch = ?")
            values.append(current_epoch)
        
        if current_loss is not None:
            updates.append("current_loss = ?")
            values.append(current_loss)
        
        if output_model_name is not None:
            updates.append("output_model_name = ?")
            values.append(output_model_name)
        
        if error_message is not None:
            updates.append("error_message = ?")
            values.append(error_message)
        
        task = self.get_task(task_id)
        if not task:
            return None
        
        if status == 'running' and not task.get('started_at'):
            updates.append("started_at = ?")
            values.append(datetime.now().isoformat())
        
        if status in ['completed', 'failed']:
            updates.append("completed_at = ?")
            values.append(datetime.now().isoformat())
        
        values.append(task_id)
        
        cursor.execute(f"""
            UPDATE training_tasks 
            SET {', '.join(updates)} 
            WHERE id = ?
        """, values)
        conn.commit()
        
        logger.info(f"Training task status updated: {task_id} - {status}")
        return self.get_task(task_id)
    
    def delete_task(self, task_id: str) -> bool:
        """Delete training task"""
        conn = self.db.get_connection()
        cursor = conn.cursor()
        cursor.execute("DELETE FROM training_tasks WHERE id = ?", (task_id,))
        conn.commit()
        
        logger.info(f"Training task deleted: {task_id}")
        return True


class ModelSwitchService:
    """Model Switch service - convenient model switching"""
    
    def __init__(self):
        self.db = get_database()
    
    def get_current_model(self, model_type: str = 'llm') -> Optional[Dict[str, Any]]:
        """Get current active model"""
        conn = self.db.get_connection()
        cursor = conn.cursor()
        
        # First check if there's a default model
        cursor.execute("""
            SELECT m.*, p.display_name as provider_name 
            FROM models m 
            LEFT JOIN model_providers p ON m.provider_id = p.id
            WHERE m.model_type = ? AND m.is_default = 1 AND m.status = 'active'
            ORDER BY m.is_default DESC
            LIMIT 1
        """, (model_type,))
        row = cursor.fetchone()
        
        if row:
            result = dict(row)
            if result.get('strengths'):
                try:
                    result['strengths'] = json.loads(result['strengths'])
                except:
                    pass
            return result
        
        # Fallback to first active model
        cursor.execute("""
            SELECT m.*, p.display_name as provider_name 
            FROM models m 
            LEFT JOIN model_providers p ON m.provider_id = p.id
            WHERE m.model_type = ? AND m.status = 'active'
            ORDER BY m.is_default DESC
            LIMIT 1
        """, (model_type,))
        row = cursor.fetchone()
        
        if not row:
            return None
        
        result = dict(row)
        if result.get('strengths'):
            try:
                result['strengths'] = json.loads(result['strengths'])
            except:
                pass
        return result
    
    def switch_model(self, model_id: str) -> Dict[str, Any]:
        """Switch to a different model"""
        # Get model info first
        conn = self.db.get_connection()
        cursor = conn.cursor()
        cursor.execute("""
            SELECT model_type FROM models WHERE id = ?
        """, (model_id,))
        row = cursor.fetchone()
        
        if not row:
            return {'success': False, 'error': 'Model not found'}
        
        model_type = row['model_type']
        
        # Get provider_id for this model
        cursor.execute("""
            SELECT provider_id FROM models WHERE id = ?
        """, (model_id,))
        row = cursor.fetchone()
        provider_id = row['provider_id']
        
        # Unset all defaults for this provider and type
        cursor.execute("""
            UPDATE models SET is_default = 0 
            WHERE provider_id = ? AND model_type = ?
        """, (provider_id, model_type))
        
        # Set the new default
        cursor.execute("""
            UPDATE models SET is_default = 1 WHERE id = ?
        """, (model_id,))
        conn.commit()
        
        logger.info(f"Model switched to: {model_id}")
        
        # Return new model info
        model_service = ModelManagementService()
        return {'success': True, 'model': model_service.get_model(model_id)}
    
    def list_available_models(self, model_type: str = 'llm') -> List[Dict[str, Any]]:
        """List all available models for switching"""
        model_service = ModelManagementService()
        return model_service.list_models(status='active', model_type=model_type)


# Singleton instances
_provider_service = None
_model_service = None
_fine_tune_service = None
_training_service = None
_model_switch_service = None


def get_provider_service() -> ModelProviderService:
    """Get model provider service singleton"""
    global _provider_service
    if _provider_service is None:
        _provider_service = ModelProviderService()
    return _provider_service


def get_model_service() -> ModelManagementService:
    """Get model management service singleton"""
    global _model_service
    if _model_service is None:
        _model_service = ModelManagementService()
    return _model_service


def get_fine_tune_service() -> FineTuneService:
    """Get fine-tune service singleton"""
    global _fine_tune_service
    if _fine_tune_service is None:
        _fine_tune_service = FineTuneService()
    return _fine_tune_service


def get_training_service() -> TrainingService:
    """Get training service singleton"""
    global _training_service
    if _training_service is None:
        _training_service = TrainingService()
    return _training_service


def get_model_switch_service() -> ModelSwitchService:
    """Get model switch service singleton"""
    global _model_switch_service
    if _model_switch_service is None:
        _model_switch_service = ModelSwitchService()
    return _model_switch_service
