import sqlite3
from datetime import datetime
from typing import List, Tuple, Optional


class Database:
    def __init__(self, db_name: str = "income_bot.db"):
        self.db_name = db_name
        self.init_database()

    def get_connection(self):
        """Получить соединение с базой данных"""
        conn = sqlite3.connect(self.db_name)
        conn.row_factory = sqlite3.Row
        return conn

    def init_database(self):
        """Инициализация базы данных - создание таблиц"""
        conn = self.get_connection()
        cursor = conn.cursor()

        # Таблица категорий
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS categories (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL UNIQUE,
                user_id INTEGER NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)

        # Таблица транзакций
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS transactions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                category_id INTEGER NOT NULL,
                amount REAL NOT NULL,
                transaction_date DATE NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (category_id) REFERENCES categories(id)
            )
        """)

        # Создаем начальные категории для всех пользователей
        default_categories = ["ПТТ", "ПРИОРИТЕТ", "СТАНКИ", "СКИПЕТР"]
        for category_name in default_categories:
            cursor.execute("""
                INSERT OR IGNORE INTO categories (name, user_id) 
                VALUES (?, 0)
            """, (category_name,))

        conn.commit()
        conn.close()

    def add_category(self, user_id: int, category_name: str) -> bool:
        """Добавить новую категорию"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        category_name = category_name.upper()
        
        # Проверяем, существует ли уже такая категория (общая или пользовательская)
        cursor.execute("""
            SELECT id FROM categories 
            WHERE name = ? AND (user_id = ? OR user_id = 0)
        """, (category_name, user_id))
        
        if cursor.fetchone():
            conn.close()
            return False
        
        try:
            cursor.execute("""
                INSERT INTO categories (name, user_id) 
                VALUES (?, ?)
            """, (category_name, user_id))
            conn.commit()
            return True
        except sqlite3.IntegrityError:
            return False
        finally:
            conn.close()

    def get_categories(self, user_id: int) -> List[str]:
        """Получить список всех категорий пользователя"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        # Получаем категории пользователя и общие категории (user_id=0)
        cursor.execute("""
            SELECT DISTINCT name FROM categories 
            WHERE user_id = ? OR user_id = 0
            ORDER BY name
        """, (user_id,))
        
        categories = [row[0] for row in cursor.fetchall()]
        conn.close()
        return categories

    def get_category_id(self, user_id: int, category_name: str) -> Optional[int]:
        """Получить ID категории по имени"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT id FROM categories 
            WHERE name = ? AND (user_id = ? OR user_id = 0)
            LIMIT 1
        """, (category_name.upper(), user_id))
        
        row = cursor.fetchone()
        conn.close()
        return row[0] if row else None

    def add_transaction(self, user_id: int, category_name: str, amount: float, transaction_date: str) -> bool:
        """Добавить транзакцию"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        category_id = self.get_category_id(user_id, category_name)
        if not category_id:
            conn.close()
            return False

        try:
            cursor.execute("""
                INSERT INTO transactions (user_id, category_id, amount, transaction_date)
                VALUES (?, ?, ?, ?)
            """, (user_id, category_id, amount, transaction_date))
            conn.commit()
            return True
        except Exception as e:
            print(f"Error adding transaction: {e}")
            return False
        finally:
            conn.close()

    def get_total_by_category(self, user_id: int, category_name: str) -> float:
        """Получить общую сумму по категории"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        category_id = self.get_category_id(user_id, category_name)
        if not category_id:
            conn.close()
            return 0.0

        cursor.execute("""
            SELECT COALESCE(SUM(amount), 0) as total
            FROM transactions
            WHERE user_id = ? AND category_id = ?
        """, (user_id, category_id))
        
        result = cursor.fetchone()
        conn.close()
        return result[0] if result else 0.0

    def get_monthly_statistics(self, user_id: int, year: int, month: int) -> List[Tuple[str, float]]:
        """Получить статистику за месяц"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT c.name, COALESCE(SUM(t.amount), 0) as total
            FROM categories c
            LEFT JOIN transactions t ON c.id = t.category_id 
                AND t.user_id = ? 
                AND strftime('%Y', t.transaction_date) = ? 
                AND strftime('%m', t.transaction_date) = ?
            WHERE c.user_id = ? OR c.user_id = 0
            GROUP BY c.id, c.name
            HAVING total > 0
            ORDER BY total DESC
        """, (user_id, str(year), f"{month:02d}", user_id))
        
        results = [(row[0], row[1]) for row in cursor.fetchall()]
        conn.close()
        return results

    def get_all_statistics(self, user_id: int) -> List[Tuple[str, float]]:
        """Получить общую статистику"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT c.name, COALESCE(SUM(t.amount), 0) as total
            FROM categories c
            LEFT JOIN transactions t ON c.id = t.category_id AND t.user_id = ?
            WHERE c.user_id = ? OR c.user_id = 0
            GROUP BY c.id, c.name
            HAVING total > 0
            ORDER BY total DESC
        """, (user_id, user_id))
        
        results = [(row[0], row[1]) for row in cursor.fetchall()]
        conn.close()
        return results

    def get_total_amount(self, user_id: int) -> float:
        """Получить общую сумму всех доходов"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT COALESCE(SUM(amount), 0) as total
            FROM transactions
            WHERE user_id = ?
        """, (user_id,))
        
        result = cursor.fetchone()
        conn.close()
        return result[0] if result else 0.0

    def get_month_total(self, user_id: int, year: int, month: int) -> float:
        """Получить общую сумму за месяц"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT COALESCE(SUM(amount), 0) as total
            FROM transactions
            WHERE user_id = ? 
            AND strftime('%Y', transaction_date) = ?
            AND strftime('%m', transaction_date) = ?
        """, (user_id, str(year), f"{month:02d}"))
        
        result = cursor.fetchone()
        conn.close()
        return result[0] if result else 0.0

    def get_recent_transactions(self, user_id: int, limit: int = 10) -> List[Tuple[int, str, float, str]]:
        """Получить последние транзакции пользователя"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT t.id, c.name, t.amount, t.transaction_date
            FROM transactions t
            JOIN categories c ON t.category_id = c.id
            WHERE t.user_id = ?
            ORDER BY t.created_at DESC
            LIMIT ?
        """, (user_id, limit))
        
        results = [(row[0], row[1], row[2], row[3]) for row in cursor.fetchall()]
        conn.close()
        return results

    def get_transaction(self, transaction_id: int, user_id: int) -> Optional[Tuple[int, str, float, str]]:
        """Получить транзакцию по ID"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT t.id, c.name, t.amount, t.transaction_date
            FROM transactions t
            JOIN categories c ON t.category_id = c.id
            WHERE t.id = ? AND t.user_id = ?
        """, (transaction_id, user_id))
        
        row = cursor.fetchone()
        conn.close()
        return (row[0], row[1], row[2], row[3]) if row else None

    def delete_transaction(self, transaction_id: int, user_id: int) -> bool:
        """Удалить транзакцию"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        try:
            # Проверяем, что транзакция принадлежит пользователю
            cursor.execute("""
                SELECT id FROM transactions 
                WHERE id = ? AND user_id = ?
            """, (transaction_id, user_id))
            
            if not cursor.fetchone():
                conn.close()
                return False
            
            cursor.execute("""
                DELETE FROM transactions 
                WHERE id = ? AND user_id = ?
            """, (transaction_id, user_id))
            
            conn.commit()
            return cursor.rowcount > 0
        except Exception as e:
            print(f"Error deleting transaction: {e}")
            return False
        finally:
            conn.close()
