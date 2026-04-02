from backend.app.services.day_brief import build_day_brief_payload


def _build_payload():
    return build_day_brief_payload(
        {
            'personalization_level': 'personalized_v2',
            'meta': {'fallback_mode': False},
            'timezone': 'Europe/Moscow',
            'location_label': 'Мончегорск, Россия',
            'moon_sign': 'Весы',
            'moon_phase': 'Полнолуние',
            'moon_emoji': '🌕',
            'aspects_count': 2,
            'traffic_lights': {'health': 'green', 'money': 'green', 'love': 'green'},
            'fast_hits': [
                {'transit': 'Mercury', 'natal': 'Mercury', 'type': 'Тригон (120°)', 'summary': 'Меркурий Тригон (120°) Меркурий'},
                {'transit': 'Sun', 'natal': 'Mars', 'type': 'Тригон (120°)', 'summary': 'Солнце Тригон (120°) Марс'},
            ],
            'semantic_layer': {
                'headline': 'День про проще собрать мысль, договориться о деталях и сшить разрозненные вводные: хороший результат дает короткий и взрослый ход.',
                'practical_move': 'Двигай одну покупку, одно условие или одну рабочую задачу, а остальное оставь в фоне.',
                'pacing': 'рабочий темп держится на одном-двух приоритетах, без расползания в суету',
                'rest': 'силы лучше держатся на ровном темпе, чем на вспышках',
                'money_admin_focus': 'рабочие и денежные вопросы лучше собирать по одному, а не параллельной пачкой',
                'relationship_softness': 'отношения сегодня любят ясность без нажима и без скрытых проверок',
                'focus_key': 'launch',
                'friction': 'распыление внимания, лишние обещания и попытка решить все одним рывком',
            },
        },
        user=None,
        generation_mode='deterministic',
    )


def test_day_brief_score_supporting_factors_use_selected_explainability_when_personalized_lookup_is_sparse() -> None:
    payload = _build_payload()
    scores = {item['key']: item for item in payload['scores']}

    assert scores['energy']['details']['supporting_factors']
    assert scores['money']['details']['supporting_factors']
    assert scores['love']['details']['supporting_factors']
    assert any('Солнце Тригон (120°) Марс' in (factor.get('label') or '') for factor in scores['energy']['details']['supporting_factors'])
    assert any('Рабочий контекст' == (factor.get('label') or '') for factor in scores['money']['details']['supporting_factors'])
    assert any('Контакт и тон' == (factor.get('label') or '') for factor in scores['love']['details']['supporting_factors'])


def test_day_brief_score_supporting_factors_hide_raw_status_and_semantic_labels() -> None:
    payload = _build_payload()
    labels = [
        factor.get('label') or ''
        for score in payload['scores']
        for factor in score['details']['supporting_factors']
    ]

    assert 'money:green' not in labels
    assert 'love:green' not in labels
    assert not any(label.startswith('День про проще собрать мысль') for label in labels)
    assert 'Фокус дня' in labels
