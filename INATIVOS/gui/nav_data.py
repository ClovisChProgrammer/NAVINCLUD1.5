import os
import json
import threading
import pandas as pd
from field_discovery import FieldDiscoverer, TypoCorrector


def extract_tests_from_data(data, filename, directory):
    """Extrai testes de dados que podem ser lista ou dict."""
    required = ['testId', 'timestamp', 'testResults', 'preTest']
    valid = []
    
    if isinstance(data, list):
        for item in data:
            if isinstance(item, dict) and all(k in item for k in required):
                corrected = TypoCorrector.correct_nested(item)
                corrected['_source_file'] = filename
                corrected['_source_dir'] = directory
                valid.append(corrected)
    
    elif isinstance(data, dict):
        if all(k in data for k in required):
            corrected = TypoCorrector.correct_nested(data)
            corrected['_source_file'] = filename
            corrected['_source_dir'] = directory
            valid.append(corrected)
        else:
            for key, value in data.items():
                if isinstance(value, dict) and all(k in value for k in required):
                    corrected = TypoCorrector.correct_nested(value)
                    corrected['_source_file'] = filename
                    corrected['_source_dir'] = directory
                    valid.append(corrected)
    
    return valid


class NavData:
    def __init__(self):
        self.directories = []
        self.records = []
        self.metadata = {}
        self.fields_info = {}
        self.categorized = {}
        self.df = pd.DataFrame()
        self.loaded_count = 0
        self.error_count = 0
        self._lock = threading.Lock()
        self._seen_test_ids = set()

    def load_directory(self, directory, progress_callback=None):
        loaded = []
        duplicates_ignored = 0
        terminal_count = {}
        error_count = 0

        if not os.path.isdir(directory):
            raise FileNotFoundError(f'Diretorio nao encontrado: {directory}')

        files = [f for f in os.listdir(directory)
                 if (f.startswith('navinclud_') or f.startswith('resultados_')) 
                 and f.endswith('.json')]

        for i, filename in enumerate(files):
            filepath = os.path.join(directory, filename)
            try:
                with open(filepath, 'r', encoding='utf-8-sig') as f:
                    data = json.load(f)

                valid = extract_tests_from_data(data, filename, directory)
                
                if valid:
                    for t in valid:
                        test_id = t.get('testId')
                        if test_id and test_id not in self._seen_test_ids:
                            self._seen_test_ids.add(test_id)
                            loaded.append(t)
                            tid = t.get('terminalId', 'unknown')
                            terminal_count[tid] = terminal_count.get(tid, 0) + 1
                        else:
                            duplicates_ignored += 1
                else:
                    error_count += 1
            except (json.JSONDecodeError, Exception):
                error_count += 1

            if progress_callback:
                progress_callback(i + 1, len(files))

        with self._lock:
            self.records.extend(loaded)
            self.metadata[directory] = {
                'files': len(files),
                'valid': len(loaded),
                'duplicates_ignored': duplicates_ignored,
                'errors': error_count,
                'terminals': len(terminal_count),
            }
            self.directories.append(directory)
            self.loaded_count += len(loaded)
            self.error_count += error_count

        self._rebuild_df()
        return len(loaded), error_count

    def _rebuild_df(self):
        corrected_records = [TypoCorrector.correct_nested(r) for r in self.records]
        flat_records = []
        for record in corrected_records:
            flat_records.append(FieldDiscoverer.flatten(record))

        self.df = pd.DataFrame(flat_records)

        self.fields_info, self.categorized = FieldDiscoverer.discover(self.records)

        bool_fields = self.categorized.get('booleanos', [])
        for f in bool_fields:
            if f in self.df.columns:
                self.df[f] = self.df[f].astype(bool)

        array_fields = self.categorized.get('arrays', [])
        for f in array_fields:
            if f in self.df.columns:
                self.df, expanded_vals = FieldDiscoverer.expand_array_field(self.df, f)
                self.fields_info, self.categorized = FieldDiscoverer.discover(self.records)
                for val in expanded_vals:
                    col = f'{f}.{val}'
                    self.categorized['booleanos'].append(col)

    def get_summary_stats(self):
        total = len(self.df) if not self.df.empty else 0
        if total == 0:
            return {'total': 0, 'normal_count': 0, 'deficient_count': 0,
                    'terminal_count': 0, 'avg_percent': 0}

        normal = self.df[self.df.get('testResults.correctPercent', 0) >= 90]
        deficient = self.df[self.df.get('testResults.correctPercent', 0) < 90]

        terminal_ids = set()
        for r in self.records:
            tid = r.get('terminalId', 'unknown')
            if tid:
                terminal_ids.add(tid)

        return {
            'total': total,
            'normal_count': len(normal),
            'deficient_count': len(deficient),
            'terminal_count': len(terminal_ids),
            'avg_percent': round(self.df['testResults.correctPercent'].mean(), 1)
            if 'testResults.correctPercent' in self.df.columns else 0,
        }

    def get_fields_by_category(self):
        return FieldDiscoverer.CATEGORY_GROUPS

    def get_active_field_keys(self):
        keys = set()
        for group_fields in FieldDiscoverer.CATEGORY_GROUPS.values():
            for f in group_fields:
                if f in self.df.columns or any(c.startswith(f) for c in self.df.columns):
                    keys.add(f)
        return sorted(keys)

    def groupby_dynamic(self, group_fields, agg_fields):
        if not group_fields and not agg_fields:
            return None, 'Selecione ao menos um campo para agrupar ou agregar.'

        available_groups = [f for f in group_fields if f in self.df.columns]
        available_aggs = [f for f in agg_fields if f in self.df.columns]

        if not available_groups and not available_aggs:
            return None, 'Nenhum dos campos selecionados existe nos dados.'

        if not available_groups:
            numeric = [f for f in available_aggs
                       if f in self.categorized.get('numericos', [])]
            if numeric:
                result = self.df[numeric].agg(['mean', 'count', 'min', 'max']).T
            else:
                result = self.df[available_aggs].describe()
            result = result.reset_index()
            return result, None

        numeric_aggs = [f for f in available_aggs
                        if f in self.categorized.get('numericos', [])]

        if not numeric_aggs:
            result = self.df.groupby(available_groups).size().reset_index(name='count')
        else:
            result = self.df.groupby(available_groups)[numeric_aggs].agg(
                ['mean', 'count']
            ).round(2)
            result.columns = [f'{col[0]}_{col[1]}' for col in result.columns]
            result = result.reset_index()

        return result, None

    def get_chart_type_suggestion(self, group_fields, agg_fields):
        has_numeric = any(f in self.categorized.get('numericos', []) for f in agg_fields)
        has_categoric = any(f in self.categorized.get('categoricos', []) for f in group_fields)

        if not group_fields and has_numeric:
            return 'histograma'
        if has_categoric and not has_numeric:
            return 'pizza'
        return 'barras'
