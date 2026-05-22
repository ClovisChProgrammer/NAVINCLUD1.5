class TypoCorrector:
    TYPO_MAP = {
        'deutanopia': 'deuteranopia',
        'deutanomaly': 'deuteranomaly',
        'achromaopia': 'achromatopsia',
    }

    @classmethod
    def correct(cls, value):
        if isinstance(value, str):
            return cls.TYPO_MAP.get(value, value)
        return value

    @classmethod
    def correct_key(cls, key):
        parts = key.split('.')
        corrected = [cls.TYPO_MAP.get(p, p) for p in parts]
        return '.'.join(corrected)

    @classmethod
    def correct_nested(cls, obj):
        if isinstance(obj, dict):
            return {k: cls.correct_nested(v) for k, v in obj.items()}
        elif isinstance(obj, list):
            return [cls.correct_nested(item) for item in obj]
        elif isinstance(obj, str):
            return cls.TYPO_MAP.get(obj, obj)
        return obj


class FieldDiscoverer:
    CATEGORY_GROUPS = {
        'Pre-Teste': ['preTest.sexo', 'preTest.idade', 'preTest.turma'],
        'Resultados': ['testResults.correctCount', 'testResults.correctPercent',
                       'testResults.avgReactionTimeMs', 'testResults.totalPlates',
                       'testResults.detectedDefect', 'testResults.controlPlateErrors'],
        'Erros por Tipo': ['testResults.errorsByType.achromatomaly',
                           'testResults.errorsByType.achromatopsia',
                           'testResults.errorsByType.control',
                           'testResults.errorsByType.deuteranomaly',
                           'testResults.errorsByType.deuteranopia',
                           'testResults.errorsByType.protanomaly',
                           'testResults.errorsByType.protanopia',
                           'testResults.errorsByType.tritanomaly',
                           'testResults.errorsByType.tritanopia'],
        'Pontos por Tipo': ['testResults.scorePointsByType.achromatomaly',
                            'testResults.scorePointsByType.achromatopsia',
                            'testResults.scorePointsByType.control',
                            'testResults.scorePointsByType.deuteranomaly',
                            'testResults.scorePointsByType.deuteranopia',
                            'testResults.scorePointsByType.protanomaly',
                            'testResults.scorePointsByType.protanopia',
                            'testResults.scorePointsByType.tritanomaly',
                            'testResults.scorePointsByType.tritanopia'],
        'Filtro Aplicado': ['appliedFilter.enabled', 'appliedFilter.intensity',
                            'appliedFilter.shift', 'appliedFilter.type'],
        'Pos-Teste': ['normalPostTest.alreadyTaken',
                      'experiencePostTest.visualImprovement',
                      'experiencePostTest.navigationEase',
                      'experiencePostTest.wouldRecommend',
                      'experiencePostTest.comfortLevel'],
        'Percepcao': ['testResults.testPerception'],
    }

    @staticmethod
    def flatten(obj, prefix=''):
        fields = {}
        if isinstance(obj, dict):
            for k, v in obj.items():
                corrected_k = TypoCorrector.correct(k)
                full = f'{prefix}.{corrected_k}' if prefix else corrected_k
                if isinstance(v, dict):
                    fields.update(FieldDiscoverer.flatten(v, full))
                elif isinstance(v, list):
                    fields[full] = v
                else:
                    fields[full] = v
        return fields

    @staticmethod
    def discover(records):
        all_fields = {}
        for record in records:
            corrected = TypoCorrector.correct_nested(record)
            flat = FieldDiscoverer.flatten(corrected)
            for k, v in flat.items():
                if k not in all_fields:
                    all_fields[k] = {'types': set(), 'values': set(),
                                     'present_in': 0, 'absent_in': 0}
                all_fields[k]['types'].add(type(v).__name__)
                if isinstance(v, list):
                    all_fields[k]['values'].add(tuple(v))
                else:
                    all_fields[k]['values'].add(v)
                all_fields[k]['present_in'] += 1

        for record in records:
            corrected = TypoCorrector.correct_nested(record)
            flat_keys = set(FieldDiscoverer.flatten(corrected).keys())
            for k in all_fields:
                if k not in flat_keys:
                    all_fields[k]['absent_in'] += 1

        total = len(records)
        categorized = {'categoricos': [], 'numericos': [],
                       'booleanos': [], 'arrays': [], 'constantes': [],
                       'opcionais': []}

        for k, v in sorted(all_fields.items()):
            is_constant = len(v['values']) <= 1
            is_optional = v['present_in'] < total

            if is_constant:
                categorized['constantes'].append(k)
                continue

            if is_optional:
                categorized['opcionais'].append(k)

            if 'bool' in v['types']:
                categorized['booleanos'].append(k)
            elif 'int' in v['types'] or 'float' in v['types']:
                categorized['numericos'].append(k)
            elif 'list' in v['types']:
                categorized['arrays'].append(k)
            else:
                categorized['categoricos'].append(k)

        return all_fields, categorized

    @staticmethod
    def expand_array_field(df, field_name):
        values_set = set()
        for row in df[field_name].dropna():
            if isinstance(row, list):
                values_set.update(row)
        for val in sorted(values_set):
            col = f'{field_name}.{val}'
            if col not in df.columns:
                df[col] = df[field_name].apply(
                    lambda x: 1 if isinstance(x, list) and val in x else 0
                )
        return df, sorted(values_set)

    @staticmethod
    def get_display_name(field_key):
        mapping = {
            'preTest.sexo': 'Sexo',
            'preTest.idade': 'Idade',
            'preTest.turma': 'Turma',
            'testResults.correctCount': 'Acertos',
            'testResults.correctPercent': '% Acertos',
            'testResults.avgReactionTimeMs': 'Tempo Medio (ms)',
            'testResults.totalPlates': 'Total de Placas',
            'testResults.detectedDefect': 'Defeito Detectado',
            'testResults.controlPlateErrors': 'Erro em Controle',
            'appliedFilter.enabled': 'Filtro Ativado',
            'appliedFilter.intensity': 'Intensidade do Filtro',
            'appliedFilter.shift': 'Shift do Filtro',
            'appliedFilter.type': 'Tipo de Filtro',
            'normalPostTest.alreadyTaken': 'Ja fez o teste',
            'experiencePostTest.visualImprovement': 'Melhora Visual',
            'experiencePostTest.navigationEase': 'Facilidade Navegacao',
            'experiencePostTest.wouldRecommend': 'Recomendaria',
            'experiencePostTest.comfortLevel': 'Conforto',
        }
        if field_key in mapping:
            return mapping[field_key]
        short = field_key.split('.')[-1]
        return short
