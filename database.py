import json
import os
import uuid
from datetime import datetime
from threading import Lock

class Database:
    """Simple file-based database for emissions data"""
    
    def __init__(self, db_file='data/emissions.json'):
        self.db_file = db_file
        self.lock = Lock()
        self._ensure_db()
        self.data = self._load_data()
    
    def _ensure_db(self):
        """Ensure database file and directory exist"""
        os.makedirs(os.path.dirname(self.db_file) or '.', exist_ok=True)
        if not os.path.exists(self.db_file):
            with open(self.db_file, 'w') as f:
                json.dump({'emissions': []}, f)
    
    def _load_data(self):
        """Load data from JSON file"""
        try:
            with open(self.db_file, 'r') as f:
                return json.load(f)
        except Exception as e:
            print(f"Error loading data: {str(e)}")
            return {'emissions': []}
    
    def _save_data(self):
        """Save data to JSON file"""
        try:
            with self.lock:
                with open(self.db_file, 'w') as f:
                    json.dump(self.data, f, indent=2)
        except Exception as e:
            print(f"Error saving data: {str(e)}")
    
    def add_emission(self, emission_data):
        """Add new emission record"""
        emission_id = str(uuid.uuid4())
        
        entry = {
            'id': emission_id,
            'type': emission_data.get('type', ''),
            'value': emission_data.get('value', 0),
            'emissions': emission_data.get('emissions', 0),
            'date': emission_data.get('date', datetime.now().isoformat()),
            'notes': emission_data.get('notes', ''),
            'category': emission_data.get('category', 'general'),
            'created_at': datetime.now().isoformat()
        }
        
        self.data['emissions'].append(entry)
        self._save_data()
        return entry
    
    def get_all_emissions(self):
        """Get all emission records"""
        return self.data.get('emissions', [])
    
    def get_emission_by_id(self, emission_id):
        """Get specific emission record by ID"""
        for emission in self.data.get('emissions', []):
            if emission['id'] == emission_id:
                return emission
        return None
    
    def delete_emission(self, emission_id):
        """Delete emission record by ID"""
        self.data['emissions'] = [
            e for e in self.data['emissions'] if e['id'] != emission_id
        ]
        self._save_data()
        return True
    
    def update_emission(self, emission_id, updated_data):
        """Update emission record"""
        for i, emission in enumerate(self.data['emissions']):
            if emission['id'] == emission_id:
                self.data['emissions'][i].update(updated_data)
                self._save_data()
                return self.data['emissions'][i]
        return None
    
    def get_emissions_by_type(self, activity_type):
        """Get emissions filtered by activity type"""
        return [e for e in self.data['emissions'] if e['type'] == activity_type]
    
    def get_emissions_by_category(self, category):
        """Get emissions filtered by category"""
        return [e for e in self.data['emissions'] if e['category'] == category]
    
    def get_emissions_by_date_range(self, start_date, end_date):
        """Get emissions within date range"""
        emissions = []
        for emission in self.data['emissions']:
            try:
                emit_date = datetime.fromisoformat(emission['date'])
                if start_date <= emit_date <= end_date:
                    emissions.append(emission)
            except ValueError:
                continue
        return emissions
    
    def get_statistics(self):
        """Get database statistics"""
        emissions = self.data.get('emissions', [])
        if not emissions:
            return {
                'total_records': 0,
                'total_emissions_kg': 0,
                'average_emission': 0,
                'min_emission': 0,
                'max_emission': 0
            }
        
        total_emissions = sum(e['emissions'] for e in emissions)
        avg_emissions = total_emissions / len(emissions)
        min_emission = min(e['emissions'] for e in emissions)
        max_emission = max(e['emissions'] for e in emissions)
        
        return {
            'total_records': len(emissions),
            'total_emissions_kg': round(total_emissions, 2),
            'average_emission_kg': round(avg_emissions, 2),
            'min_emission_kg': round(min_emission, 2),
            'max_emission_kg': round(max_emission, 2)
        }
    
    def clear_all(self):
        """Clear all emissions data (use with caution)"""
        self.data = {'emissions': []}
        self._save_data()
        return True
    
    def export_to_csv(self, filename='emissions_export.csv'):
        """Export data to CSV file"""
        try:
            import csv
            emissions = self.data.get('emissions', [])
            
            if not emissions:
                return False
            
            with open(filename, 'w', newline='', encoding='utf-8') as f:
                fieldnames = emissions[0].keys()
                writer = csv.DictWriter(f, fieldnames=fieldnames)
                writer.writeheader()
                writer.writerows(emissions)
            
            return True
        except Exception as e:
            print(f"Error exporting to CSV: {str(e)}")
            return False
    
    def export_to_json(self, filename='emissions_export.json'):
        """Export data to JSON file"""
        try:
            emissions = self.data.get('emissions', [])
            
            with open(filename, 'w', encoding='utf-8') as f:
                json.dump(emissions, f, indent=2)
            
            return True
        except Exception as e:
            print(f"Error exporting to JSON: {str(e)}")
            return False
    
    def search_emissions(self, query):
        """Search emissions by notes or type"""
        query_lower = query.lower()
        results = []
        
        for emission in self.data['emissions']:
            if (query_lower in emission.get('type', '').lower() or
                query_lower in emission.get('notes', '').lower()):
                results.append(emission)
        
        return results
    
    def get_emissions_count(self):
        """Get total count of emissions"""
        return len(self.data.get('emissions', []))
    
    def get_last_n_emissions(self, n=10):
        """Get last N emission records"""
        emissions = self.data.get('emissions', [])
        return sorted(emissions, key=lambda x: x['date'], reverse=True)[:n]
    
    def get_daily_total(self, date_str):
        """Get total emissions for a specific date"""
        date_str = date_str.split('T')[0]  # Extract just the date part
        daily_total = 0
        
        for emission in self.data['emissions']:
            emission_date = emission['date'].split('T')[0]
            if emission_date == date_str:
                daily_total += emission['emissions']
        
        return round(daily_total, 2)
    
    def get_monthly_totals(self, year, month):
        """Get total emissions for a specific month"""
        monthly_total = 0
        count = 0
        
        for emission in self.data['emissions']:
            emission_date = datetime.fromisoformat(emission['date'])
            if emission_date.year == year and emission_date.month == month:
                monthly_total += emission['emissions']
                count += 1
        
        return {
            'total_kg': round(monthly_total, 2),
            'count': count,
            'average_kg': round(monthly_total / count, 2) if count > 0 else 0
        }
    
    def get_yearly_totals(self, year):
        """Get total emissions for a specific year"""
        yearly_total = 0
        count = 0
        
        for emission in self.data['emissions']:
            emission_date = datetime.fromisoformat(emission['date'])
            if emission_date.year == year:
                yearly_total += emission['emissions']
                count += 1
        
        return {
            'total_kg': round(yearly_total, 2),
            'count': count,
            'average_daily_kg': round(yearly_total / 365, 2)
        }
    
    def backup_database(self, backup_filename=None):
        """Create a backup of the database"""
        try:
            if backup_filename is None:
                backup_filename = f"backup_emissions_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
            
            with open(backup_filename, 'w', encoding='utf-8') as f:
                json.dump(self.data, f, indent=2)
            
            return True
        except Exception as e:
            print(f"Error creating backup: {str(e)}")
            return False
    
    def restore_database(self, backup_filename):
        """Restore database from backup"""
        try:
            with open(backup_filename, 'r', encoding='utf-8') as f:
                self.data = json.load(f)
            self._save_data()
            return True
        except Exception as e:
            print(f"Error restoring backup: {str(e)}")
            return False