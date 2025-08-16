import json
import sqlite3
import os
from datetime import datetime
from typing import Dict, List, Any, Optional
from pathlib import Path
import hashlib
import uuid

class TaskDataManager:
    """Manages persistent storage of all successful task results"""
    
    def __init__(self, db_path: str = None):
        if db_path is None:
            db_path = os.path.join(os.path.dirname(__file__), 'task_data.db')
        self.db_path = db_path
        self.init_database()
    
    def init_database(self):
        """Initialize the database with required tables"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Create main task results table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS task_results (
                id TEXT PRIMARY KEY,
                task_type TEXT NOT NULL,
                task_description TEXT,
                url TEXT,
                status TEXT NOT NULL,
                result_data TEXT NOT NULL,
                metadata TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                file_path TEXT,
                data_hash TEXT
            )
        ''')
        
        # Create scraped data table for detailed web scraping results
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS scraped_data (
                id TEXT PRIMARY KEY,
                task_id TEXT,
                url TEXT NOT NULL,
                scrape_type TEXT,
                title TEXT,
                content_type TEXT,
                data_size INTEGER,
                word_count INTEGER,
                link_count INTEGER,
                image_count INTEGER,
                table_count INTEGER,
                form_count INTEGER,
                scraped_at TIMESTAMP,
                raw_data TEXT,
                full_scraped_content TEXT,
                FOREIGN KEY (task_id) REFERENCES task_results (id)
            )
        ''')
        
        # Add full_scraped_content column if it doesn't exist
        cursor.execute("PRAGMA table_info(scraped_data)")
        columns = [col[1] for col in cursor.fetchall()]
        if 'full_scraped_content' not in columns:
            cursor.execute('''
                ALTER TABLE scraped_data ADD COLUMN full_scraped_content TEXT
            ''')
        
        # Create account creation results table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS account_results (
                id TEXT PRIMARY KEY,
                task_id TEXT,
                website TEXT,
                email TEXT,
                username TEXT,
                success BOOLEAN,
                created_at TIMESTAMP,
                credentials TEXT,
                FOREIGN KEY (task_id) REFERENCES task_results (id)
            )
        ''')
        
        # Create file operations table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS file_operations (
                id TEXT PRIMARY KEY,
                task_id TEXT,
                operation_type TEXT,
                file_path TEXT,
                file_size INTEGER,
                created_at TIMESTAMP,
                FOREIGN KEY (task_id) REFERENCES task_results (id)
            )
        ''')
        
        conn.commit()
        conn.close()
    
    def save_task_result(self, task_type: str, result_data: Any, 
                        task_description: str = None, url: str = None, 
                        metadata: Dict = None) -> str:
        """Save a successful task result to the database"""
        task_id = str(uuid.uuid4())
        
        # Convert result_data to JSON string if it's not already
        if isinstance(result_data, str):
            try:
                # Validate it's valid JSON
                json.loads(result_data)
                result_json = result_data
            except:
                # If not valid JSON, wrap it
                result_json = json.dumps({"result": result_data})
        else:
            result_json = json.dumps(result_data, ensure_ascii=False, indent=2)
        
        # Create data hash for deduplication
        data_hash = hashlib.md5(result_json.encode()).hexdigest()
        
        # Save to file system as well
        file_path = self._save_to_file(task_id, task_type, result_json)
        
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            INSERT INTO task_results 
            (id, task_type, task_description, url, status, result_data, metadata, file_path, data_hash)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            task_id,
            task_type,
            task_description,
            url,
            'success',
            result_json,
            json.dumps(metadata) if metadata else None,
            file_path,
            data_hash
        ))
        
        conn.commit()
        conn.close()
        
        return task_id
    
    def save_scraping_result(self, task_id: str, scraping_data: Dict) -> str:
        """Save detailed scraping results"""
        scrape_id = str(uuid.uuid4())
        
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Extract key information from scraping data
        url = scraping_data.get('url', '')
        scrape_type = scraping_data.get('scrape_type', 'all')
        
        # Get text content info
        text_content = scraping_data.get('data', {}).get('text_content', {})
        title = text_content.get('title', '') if text_content else ''
        
        # Get statistics
        stats = scraping_data.get('statistics', {})
        word_count = stats.get('word_count', 0)
        link_count = stats.get('total_links', 0)
        image_count = stats.get('total_images', 0)
        table_count = stats.get('total_tables', 0)
        form_count = stats.get('total_forms', 0)
        data_size = stats.get('page_size_chars', 0)
        
        cursor.execute('''
            INSERT INTO scraped_data 
            (id, task_id, url, scrape_type, title, content_type, data_size, 
             word_count, link_count, image_count, table_count, form_count, 
             scraped_at, raw_data, full_scraped_content)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            scrape_id,
            task_id,
            url,
            scrape_type,
            title,
            'web_page', # content_type
            data_size,
            word_count,
            link_count,
            image_count,
            table_count,
            form_count,
            datetime.now().isoformat(),
            json.dumps(scraping_data), # raw_data
            json.dumps(scraping_data) # full_scraped_content
         ))
        
        conn.commit()
        conn.close()
        
        return scrape_id
    
    def save_account_creation_result(self, task_id: str, account_data: Dict) -> str:
        """Save account creation results"""
        account_id = str(uuid.uuid4())
        
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            INSERT INTO account_results 
            (id, task_id, website, email, username, success, credentials)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        ''', (
            account_id,
            task_id,
            account_data.get('website', ''),
            account_data.get('credentials', {}).get('email', ''),
            account_data.get('credentials', {}).get('username', ''),
            account_data.get('success', False),
            json.dumps(account_data.get('credentials', {}))
        ))
        
        conn.commit()
        conn.close()
        
        return account_id
    
    def _save_to_file(self, task_id: str, task_type: str, data: str) -> str:
        """Save task data to file system"""
        # Create data directory if it doesn't exist
        data_dir = os.path.join(os.path.dirname(__file__), 'saved_task_data')
        os.makedirs(data_dir, exist_ok=True)
        
        # Create subdirectory for task type
        type_dir = os.path.join(data_dir, task_type)
        os.makedirs(type_dir, exist_ok=True)
        
        # Create filename with timestamp
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        filename = f"{task_id}_{timestamp}.json"
        file_path = os.path.join(type_dir, filename)
        
        # Save data to file
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(data)
        
        return file_path
    
    def get_scraped_content(self, task_id: str) -> Dict:
        """Get scraped content by task ID"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT * FROM scraped_data WHERE task_id = ?
        ''', (task_id,))
        
        result = cursor.fetchone()
        conn.close()
        
        if result:
            columns = ['id', 'task_id', 'url', 'scrape_type', 'title', 'content_type', 
                      'data_size', 'word_count', 'link_count', 'image_count', 'table_count', 
                      'form_count', 'scraped_at', 'raw_data', 'full_scraped_content']
            return dict(zip(columns, result))
        return None
    
    def get_task_results(self, user_id: int, limit: int = 100, offset: int = 0, task_type: str = None) -> List[Dict]:
        """Retrieve paginated task results (user_id accepted for compatibility, not stored in schema)."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        if task_type:
            cursor.execute('''
                SELECT * FROM task_results 
                WHERE task_type = ? 
                ORDER BY created_at DESC 
                LIMIT ? OFFSET ?
            ''', (task_type, limit, offset))
        else:
            cursor.execute('''
                SELECT * FROM task_results 
                ORDER BY created_at DESC 
                LIMIT ? OFFSET ?
            ''', (limit, offset))
        
        columns = [description[0] for description in cursor.description]
        results = [dict(zip(columns, row)) for row in cursor.fetchall()]
        
        conn.close()
        return results
    
    def get_scraped_data(self, url: str = None, limit: int = 50) -> List[Dict]:
        """Retrieve scraped data results"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        if url:
            cursor.execute('''
                SELECT * FROM scraped_data 
                WHERE url LIKE ? 
                ORDER BY scraped_at DESC 
                LIMIT ?
            ''', (f'%{url}%', limit))
        else:
            cursor.execute('''
                SELECT * FROM scraped_data 
                ORDER BY scraped_at DESC 
                LIMIT ?
            ''', (limit,))
        
        columns = [description[0] for description in cursor.description]
        results = [dict(zip(columns, row)) for row in cursor.fetchall()]
        
        conn.close()
        return results
    
    def get_task_statistics(self, user_id: int | None = None) -> Dict:
        """Get statistics about saved tasks (user_id accepted for compatibility, not stored in schema)."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Get task counts by type
        cursor.execute('''
            SELECT task_type, COUNT(*) as count 
            FROM task_results 
            GROUP BY task_type
        ''')
        task_counts = dict(cursor.fetchall())
        
        # Get total counts
        cursor.execute('SELECT COUNT(*) FROM task_results')
        total_tasks = cursor.fetchone()[0]
        
        cursor.execute('SELECT COUNT(*) FROM scraped_data')
        total_scraped = cursor.fetchone()[0]
        
        cursor.execute('SELECT COUNT(*) FROM account_results')
        total_accounts = cursor.fetchone()[0]
        
        # Get recent activity
        cursor.execute('''
            SELECT DATE(created_at) as date, COUNT(*) as count 
            FROM task_results 
            WHERE created_at >= date('now', '-7 days') 
            GROUP BY DATE(created_at) 
            ORDER BY date DESC
        ''')
        recent_activity = dict(cursor.fetchall())
        
        conn.close()
        
        return {
            'total_tasks': total_tasks,
            'total_scraped_pages': total_scraped,
            'total_accounts_created': total_accounts,
            'task_counts_by_type': task_counts,
            'recent_activity': recent_activity
        }
    
    def get_scraping_results(self, user_id: int, limit: int = 20, offset: int = 0) -> List[Dict]:
        """Get scraping results with pagination (currently not filtered by user)."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT sd.*, tr.created_at, tr.status, tr.metadata
            FROM scraped_data sd
            JOIN task_results tr ON sd.task_id = tr.id
            WHERE tr.task_type = 'web_scraping'
            ORDER BY tr.created_at DESC
            LIMIT ? OFFSET ?
        ''', (limit, offset))
        
        columns = [description[0] for description in cursor.description]
        results = [dict(zip(columns, row)) for row in cursor.fetchall()]
        
        conn.close()
        return results
    
    def get_task_by_id(self, task_id: str, user_id: int) -> Dict:
        """Get detailed information about a specific task (not filtered by user)."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Get task details
        cursor.execute('''
            SELECT * FROM task_results 
            WHERE id = ?
        ''', (task_id,))
        
        columns = [description[0] for description in cursor.description]
        task_row = cursor.fetchone()
        
        if not task_row:
            conn.close()
            return None
        
        task_details = dict(zip(columns, task_row))
        
        # Get additional data based on task type
        if task_details['task_type'] == 'web_scraping':
            cursor.execute('''
                SELECT id, task_id, url, scrape_type, title, content_type, data_size, word_count, link_count, image_count, table_count, form_count, scraped_at, raw_data, full_scraped_content FROM scraped_data WHERE task_id = ?
            ''', (task_id,))
            scraping_columns = [description[0] for description in cursor.description]
            scraping_row = cursor.fetchone()
            if scraping_row:
                task_details['scraping_details'] = dict(zip(scraping_columns, scraping_row))
        
        elif task_details['task_type'] == 'account_creation':
            cursor.execute('''
                SELECT * FROM account_results WHERE task_id = ?
            ''', (task_id,))
            account_columns = [description[0] for description in cursor.description]
            account_row = cursor.fetchone()
            if account_row:
                task_details['account_details'] = dict(zip(account_columns, account_row))
        
        conn.close()
        return task_details

# Global instance
task_manager = TaskDataManager()